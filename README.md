# TVBox Video Sources · 4K 影视源

一个单文件（`index.html`）的 **TVBox / 影视仓 / OK影视 配置发布页**：显示配置地址、一键复制、扫码导入。

> 页面内容不需要维护 —— 它会在加载时**自动读取同目录下的 [`4K视频源.md`](./4K视频源.md)** 并渲染。

- 仓库：<https://github.com/SOYS1/TVBox-Video-Sources>
- 页面（开启 Pages 后）：<https://soys1.github.io/TVBox-Video-Sources/>

---

## 目录

```
.
├── index.html      # 页面本体，一般不用动
├── 4K视频源.md      # ← 你只需要改这个
└── README.md
```

## 怎么更新源

直接编辑 `4K视频源.md`，一行一个地址，保存 / 提交即可，页面刷新后自动同步：

```md
https://9280.kstore.vip/aiwex.json
```

规则：

| 写法 | 效果 |
| --- | --- |
| `https://a.com/x.json` | **第一条自动成为主线路**（大按钮 + 二维码） |
| 第二条及以后 | 自动显示为「线路2、线路3…」备选列表 |
| `备用线路 \| https://b.com/y.json` | 自定义该线路的显示名称 |
| `- https://c.com/z.json` | markdown 列表写法也支持 |
| 空行、`#` 开头的行、```` ``` ```` 围栏 | 自动忽略（可以写注释） |

页面上的「可用线路」数量、「已同步 N 条线路」状态、「源文件更新」日期都会跟着变。

## 部署（GitHub Pages）

1. 把 `index.html`、`4K视频源.md` 放进仓库**根目录**，推到 `main` 分支。
2. 仓库 → **Settings → Pages** → Source 选 **Deploy from a branch** → Branch `main` / `/ (root)` → Save。
3. 等 1～2 分钟，访问 <https://soys1.github.io/TVBox-Video-Sources/>。

**注意：**
- 仓库必须是 **Public**（私有仓库的 Pages 需要 GitHub Pro 且默认不公开，TVBox 也拿不到）。
- Pages 有 CDN 缓存，改完 md 后最长约 10 分钟生效；急的话用无痕窗口或加 `?v=2` 访问。
- 「源文件更新」日期：在 `github.io` 上会调用 GitHub API 读取该文件的最后一次提交时间，取不到时显示 `—`。

## 本地预览

`fetch` 读本地文件需要 http 环境，**直接双击 index.html 会走内置兜底列表**（页面会提示）：

```bash
# 任选一个
python -m http.server 8000
npx serve .
```

然后打开 <http://localhost:8000/>。

## 说明

本页仅提供配置索引，不存储、不传播任何影视文件；所有内容均来自第三方公开接口，请在 24 小时内删除并支持正版。
