#!/usr/bin/env python3
"""探测各分区 md 里的源地址是否可用，生成 status.json。

页面会读 status.json，把探测失败的源在卡片上标成「暂时无法使用」。
只在结果真的变化时才重写文件，避免每天产生无意义的提交。

判定偏保守：只有明确的死链（404 / 410 / 5xx / 连不上 / 超时）才算失败；
403 / 429 这类多半是拦爬虫，记为「未知」，不会误标成不可用。

用法：
    python3 scripts/check_sources.py            # 检查，有变化才写 status.json
    python3 scripts/check_sources.py --force    # 无论有没有变化都重写
    python3 scripts/check_sources.py --dry-run  # 只打印结果，不写文件
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "status.json")

# 分区数据文件（新增分区时记得加到这里）
FILES = ["4K视频源.md", "直播源.md"]

TIMEOUT = 20
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# 这些状态码多半是 WAF / 限流挡了脚本，不代表源真的挂了 → 记为未知，不标记
UNKNOWN_CODES = {401, 403, 405, 406, 429, 503}


def sources_of(path):
    """按和前端一致的规则从 md 里取地址：一行一条，取第一个 http(s) 片段。"""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return []

    items = []
    for raw in lines:
        line = raw.strip()
        if line[:1] in ("-", "*"):
            line = line[1:].strip()
        if not line or line.startswith("#") or line.startswith("//") or line.startswith("```"):
            continue
        for part in (p.strip() for p in line.split("|")):
            low = part.lower()
            if low.startswith("http://") or low.startswith("https://"):
                items.append(part)
                break
    return items


def probe(url):
    """发一个只读 2KB 的请求，判断这个地址还活着没有。"""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "*/*", "Range": "bytes=0-2047"},
    )
    started = time.time()

    def elapsed():
        return int((time.time() - started) * 1000)

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            res.read(2048)
            code = res.status
            if 200 <= code < 400:
                return {"ok": True, "http": code, "ms": elapsed()}
            if code in UNKNOWN_CODES:
                return {"ok": None, "http": code, "ms": elapsed(), "reason": f"HTTP {code}"}
            return {"ok": False, "http": code, "ms": elapsed(), "reason": f"HTTP {code}"}
    except urllib.error.HTTPError as e:
        if e.code in UNKNOWN_CODES:
            return {"ok": None, "http": e.code, "ms": elapsed(), "reason": f"HTTP {e.code}"}
        return {"ok": False, "http": e.code, "ms": elapsed(), "reason": f"HTTP {e.code}"}
    except Exception as e:  # 超时 / DNS / 连接被拒 / TLS 错误
        msg = (str(e) or type(e).__name__).lower()
        if "timed out" in msg or "timeout" in msg:
            reason = "连接超时"
        elif "name or service" in msg or "nodename" in msg:
            reason = "域名解析失败"
        elif "refused" in msg:
            reason = "连接被拒绝"
        else:
            reason = "连接失败"
        return {"ok": False, "http": 0, "ms": elapsed(), "reason": reason}


def load_old():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    force = "--force" in sys.argv
    dry = "--dry-run" in sys.argv

    urls = []
    for name in FILES:
        for u in sources_of(os.path.join(ROOT, name)):
            if u not in urls:
                urls.append(u)

    if not urls:
        print("没在 md 里找到任何源地址")
        return 1

    print(f"共 {len(urls)} 个地址，开始探测…\n")
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(probe, urls))

    sources = {}
    for u, r in zip(urls, results):
        entry = {"ok": r["ok"]}
        if r.get("http"):
            entry["http"] = r["http"]
        if r.get("reason"):
            entry["reason"] = r["reason"]
        sources[u] = entry

        flag = "OK  " if r["ok"] is True else ("SKIP" if r["ok"] is None else "FAIL")
        extra = f"  ({r['reason']})" if r.get("reason") else ""
        print(f"{flag} {r.get('http') or '-':>4} {r.get('ms', 0):>6}ms  {u}{extra}")

    dead = sum(1 for s in sources.values() if s["ok"] is False)
    print(f"\n可用 {len(sources) - dead - sum(1 for s in sources.values() if s['ok'] is None)}"
          f" · 不可用 {dead}"
          f" · 未知 {sum(1 for s in sources.values() if s['ok'] is None)}")

    old = load_old()
    if old and old.get("sources") == sources and not force:
        print("源状态无变化，不重写 status.json")
        return 0

    data = {
        "checked": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": sources,
    }
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    if dry:
        print("\n--- dry run，未写入 ---")
        print(text)
        return 0

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"已写入 {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
