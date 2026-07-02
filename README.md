# 开源雷达 MVP

开源项目发现、中文评测、全中文教程、版本记录与安全下载信息网站。

## 构建

```bash
python3 build.py
```

生成的网站位于 `dist/`，直接打开 `dist/index.html` 即可查看。

构建不会覆盖已经存在的Markdown文章，人工修改后的评测和教程可以安全保留。

## 正式域名配置

获得域名后，修改 `data/site.json` 中的：

```json
{
  "site_url": "https://你的域名",
  "contact_email": "你的联系邮箱"
}
```

也可以在构建时通过环境变量覆盖：

```bash
SITE_URL="https://你的域名" CONTACT_EMAIL="你的邮箱" python3 build.py
```

正式发布前不能继续使用 `.example` 占位域名。

## Cloudflare Pages 部署

将目录提交到GitHub仓库后，在Cloudflare Pages中连接仓库：

- 构建命令：`python3 build.py`
- 输出目录：`dist`
- 环境变量：`SITE_URL`、`CONTACT_EMAIL`

每次推送到主分支后，Cloudflare Pages会自动重新构建并发布。`wrangler.toml`已经声明输出目录。

GitHub Actions会在每次提交和合并请求时自动：

1. 构建网站。
2. 检查全部本地链接。
3. 检查SEO描述和canonical。
4. 检查站点地图、RSS、404和部署文件。

## 内容结构

```text
data/projects.json          项目元数据与初评事实
content/<slug>/review.md    中文评测
content/<slug>/tutorial.md  全中文教程
static/                     样式和交互
dist/                       构建产物
scripts/validate_site.py    构建结果检查
.github/workflows/          GitHub自动构建
```

当前评测和教程由系统生成，统一标记为“AI初评、待人工复核”。完成真实安装测试后，应人工修改对应Markdown文件并更新验证状态。

## 首批项目

- Ollama
- LocalSend
- Stirling PDF
- Immich
- AppFlowy
- Penpot
- Jellyfin
- Vaultwarden
