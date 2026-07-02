#!/usr/bin/env python3
"""Build the Open Source Radar static website with only Python stdlib."""

from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "projects.json"
SITE_DATA = ROOT / "data" / "site.json"
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
DIST = ROOT / "dist"
TODAY = date.today().isoformat()


def load_projects() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def load_site() -> dict:
    site = json.loads(SITE_DATA.read_text(encoding="utf-8"))
    site["site_url"] = os.environ.get("SITE_URL", site["site_url"]).rstrip("/")
    site["contact_email"] = os.environ.get("CONTACT_EMAIL", site["contact_email"])
    return site


SITE = load_site()


def absolute(path: str = "") -> str:
    return urljoin(SITE["site_url"] + "/", path.lstrip("/"))


def inline(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" rel="noopener">\1</a>', value)
    return value


def markdown(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    para: list[str] = []
    in_code = False
    code: list[str] = []
    list_type = ""

    def flush_para() -> None:
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_para()
            close_list()
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not stripped:
            flush_para()
            close_list()
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            flush_para()
            close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            continue
        if stripped.startswith("> "):
            flush_para()
            close_list()
            out.append(f"<blockquote>{inline(stripped[2:])}</blockquote>")
            continue
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        unordered = re.match(r"^[-*]\s+(.+)$", stripped)
        if ordered or unordered:
            flush_para()
            target = "ol" if ordered else "ul"
            if list_type != target:
                close_list()
                out.append(f"<{target}>")
                list_type = target
            item = (ordered or unordered).group(1)
            out.append(f"<li>{inline(item)}</li>")
            continue
        para.append(stripped)

    flush_para()
    close_list()
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    return "\n".join(out)


def header(prefix: str = "") -> str:
    return f"""
    <header>
      <div class="site-header shell">
        <a class="brand" href="{prefix}index.html"><span class="brand-mark">O_</span><span>开源雷达</span></a>
        <nav>
          <a href="{prefix}projects/index.html">项目库</a>
          <a href="{prefix}categories/index.html">分类</a>
          <a href="{prefix}methodology/index.html">评测方法</a>
          <a href="{prefix}about/index.html">关于</a>
        </nav>
        <a class="nav-action" href="{prefix}projects/index.html">发现项目 →</a>
        <button class="menu" id="menuButton" aria-label="打开菜单">☰</button>
      </div>
      <div class="mobile-nav shell" id="mobileNav">
        <a href="{prefix}projects/index.html">项目库</a>
        <a href="{prefix}categories/index.html">分类</a>
        <a href="{prefix}methodology/index.html">评测方法</a>
        <a href="{prefix}about/index.html">关于</a>
      </div>
    </header>"""


def footer(prefix: str = "") -> str:
    return f"""
    <footer class="site-footer">
      <div class="shell footer-grid">
        <div><a class="brand" href="{prefix}index.html"><span class="brand-mark">O_</span><span>开源雷达</span></a>
        <p>发现项目，真实试用，诚实评价。本站不是任何项目的官方网站。</p></div>
        <div class="footer-links"><a href="{prefix}legal/index.html">法律与政策</a><a href="{prefix}methodology/index.html">评测方法</a><a href="{prefix}about/index.html">关于本站</a><span>© 2026</span></div>
      </div>
    </footer>"""


def page(
    title: str,
    body: str,
    prefix: str = "",
    description: str = "",
    canonical_path: str = "",
    page_type: str = "website",
    robots: str = "index,follow,max-image-preview:large",
) -> str:
    desc = html.escape(description or "开源项目中文评测、教程、版本与安全下载信息。", quote=True)
    full_title = f"{title}｜{SITE['name']}"
    canonical = absolute(canonical_path)
    structured = {
        "@context": "https://schema.org",
        "@type": "WebSite" if page_type == "website" else "Article",
        "name": full_title,
        "url": canonical,
        "description": description or SITE["description"],
        "inLanguage": SITE["language"],
        "publisher": {"@type": "Organization", "name": SITE["name"], "url": absolute()},
    }
    if page_type == "article":
        structured["dateModified"] = TODAY
        structured["author"] = {"@type": "Organization", "name": SITE["author"]}
    return f"""<!doctype html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{desc}">
<meta name="robots" content="{robots}">
<meta property="og:locale" content="zh_CN"><meta property="og:type" content="{page_type}">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{html.escape(full_title, quote=True)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{absolute('assets/social-card.svg')}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(full_title, quote=True)}">
<meta name="twitter:description" content="{desc}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/rss+xml" title="{SITE['name']} RSS" href="{absolute('rss.xml')}">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<title>{html.escape(full_title)}</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
<script type="application/ld+json">{json.dumps(structured, ensure_ascii=False).replace("</", "<\\/")}</script>
</head><body>{header(prefix)}<main>{body}</main>{footer(prefix)}
<script src="{prefix}assets/site.js"></script></body></html>"""


def score(project: dict) -> float:
    return round(sum(project["scores"].values()) / len(project["scores"]), 1)


def project_card(project: dict, prefix: str = "") -> str:
    searchable = " ".join([
        project["name"], project["tagline"], project["category"],
        project["summary"], *project["platforms"]
    ])
    return f"""
    <article class="project-card" data-search="{html.escape(searchable, quote=True)}" data-category="{project['category_slug']}">
      <div class="project-top">
        <div class="project-icon" style="--accent:{project['accent']}">{project['letter']}</div>
        <span class="stars">★ {project['stars']}</span>
      </div>
      <div class="category">{project['category']} · {project['license']}</div>
      <h3><a href="{prefix}projects/{project['slug']}/index.html">{project['name']}</a></h3>
      <p>{project['tagline']}。{project['summary']}</p>
      <div class="project-footer"><span>综合初评 {score(project)}</span><a href="{prefix}projects/{project['slug']}/index.html">查看项目 →</a></div>
      <span class="review-state">AI 初评 · 待人工复核</span>
    </article>"""


def generate_markdown(project: dict) -> tuple[str, str]:
    strengths = "\n".join(f"- {item}" for item in project["strengths"])
    cautions = "\n".join(f"- {item}" for item in project["cautions"])
    steps = "\n".join(f"{index}. {item}" for index, item in enumerate(project["steps"], 1))
    platforms = "、".join(project["platforms"])
    review = f"""# {project['name']} 中文初评

> 内容状态：AI 根据官方资料生成的初评草稿，尚未完成全部平台的人工实测。最后整理：{TODAY}。

## 一句话结论

{project['verdict']}

## 它解决什么问题

{project['summary']}

适用人群：{project['best_for']}

## 基本信息

- GitHub 仓库：[{project['repo']}]({project['github']})
- 当前记录版本：{project['version']}
- 许可证：{project['license']}
- 支持平台：{platforms}
- GitHub 星标：约 {project['stars']}（采集于 {TODAY}，会随时间变化）

## 值得关注的优点

{strengths}

## 使用前必须知道的问题

{cautions}

## 初步评价

{project['name']} 的价值并不只由 Star 数量决定。当前初评重点考察了项目定位、官方文档、许可证、平台覆盖和维护状态，但性能、稳定性、长期使用成本仍需要真实设备测试。

## 后续人工实测计划

1. 在项目主要支持平台完成安装。
2. 使用真实但非敏感数据完成核心工作流。
3. 记录安装时间、资源占用、失败步骤和恢复方式。
4. 将本页“AI初评”升级为“人工已验证”，并补充截图与测试环境。

## 编辑结论

{project['verdict']}
"""
    tutorial = f"""# {project['name']} 全中文入门教程

> 适用版本：{project['version']}。本文是首版教程草稿，正式操作前请同时核对上游文档。最后整理：{TODAY}。

## 开始之前

{project['best_for']}

支持平台：{platforms}。

## 推荐入门流程

{steps}

## 第一次使用的验证标准

- 软件或服务能够正常启动。
- 核心功能使用测试数据完成一次闭环。
- 知道配置、数据和日志保存在哪里。
- 知道如何备份、升级和卸载。
- 涉及重要数据时，已经完成恢复测试。

## 常见误区

{cautions}

## 安全与隐私

开源不自动等于安全。安装前应确认下载来源、版本、许可证和校验值；自托管项目还需要维护 HTTPS、备份、账户权限与安全更新。

## 获取官方帮助

- [GitHub 项目主页]({project['github']})
- [项目官方网站或文档]({project['official']})

## 本教程还缺什么

当前版本用于验证网站内容结构。后续人工实测将补充逐步截图、具体安装命令、不同系统差异、性能数据和真实故障处理过程。
"""
    return review, tutorial


def ensure_content(projects: list[dict]) -> None:
    for project in projects:
        directory = CONTENT / project["slug"]
        directory.mkdir(parents=True, exist_ok=True)
        review, tutorial = generate_markdown(project)
        review_path = directory / "review.md"
        tutorial_path = directory / "tutorial.md"
        if not review_path.exists():
            review_path.write_text(review, encoding="utf-8")
        if not tutorial_path.exists():
            tutorial_path.write_text(tutorial, encoding="utf-8")


def project_hero(project: dict, active: str, prefix: str) -> str:
    project_root = f"{prefix}projects/{project['slug']}/"
    tabs = [
        ("项目概览", "index.html", "overview"),
        ("中文评测", "review/index.html", "review"),
        ("使用教程", "tutorial/index.html", "tutorial"),
        ("版本下载", "downloads/index.html", "downloads"),
    ]
    tab_html = "".join(
        f'<a class="{"active" if key == active else ""}" href="{project_root}{url}">{label}</a>'
        for label, url, key in tabs
    )
    return f"""
    <section class="page-hero"><div class="shell">
      <div class="breadcrumbs"><a href="{prefix}index.html">首页</a> / <a href="{prefix}projects/index.html">项目库</a> / {project['name']}</div>
      <div class="project-title">
        <div class="project-icon" style="--accent:{project['accent']}">{project['letter']}</div>
        <div><h1>{project['name']}</h1><p>{project['tagline']}</p></div>
        <div class="score-badge"><strong>{score(project)}</strong>综合初评</div>
      </div>
      <div class="tabs">{tab_html}</div>
    </div></section>"""


def sidebar(project: dict) -> str:
    score_rows = "".join(
        f'<div class="score-row"><span>{name}</span><i style="--score:{value * 10}%"></i><b>{value}</b></div>'
        for name, value in project["scores"].items()
    )
    platforms = " / ".join(project["platforms"])
    return f"""
    <aside class="sidebar">
      <div class="notice">当前内容为AI初评草稿，不代表已经完成全部平台实测。涉及密码、照片等重要数据时，请等待人工复核。</div>
      <div class="side-card"><h3>项目信息</h3>
        <div class="meta-row"><span>Star</span><b>{project['stars']}</b></div>
        <div class="meta-row"><span>许可证</span><b>{project['license']}</b></div>
        <div class="meta-row"><span>记录版本</span><b>{project['version']}</b></div>
        <div class="meta-row"><span>平台</span><b>{platforms}</b></div>
        <a class="button acid" href="{project['github']}" rel="noopener">访问 GitHub ↗</a>
      </div>
      <div class="side-card"><h3>维度评分</h3>{score_rows}</div>
    </aside>"""


def overview(project: dict, prefix: str) -> str:
    strengths = "".join(f"<li>{html.escape(item)}</li>" for item in project["strengths"])
    cautions = "".join(f"<li>{html.escape(item)}</li>" for item in project["cautions"])
    body = f"""
    {project_hero(project, "overview", prefix)}
    <div class="shell content-layout">
      <article class="prose">
        <p class="eyebrow">{project['category']} / EDITORIAL PREVIEW</p>
        <h2>项目定位</h2><p>{project['summary']}</p>
        <h2>适合谁</h2><p>{project['best_for']}</p>
        <h2>初步优势</h2><ul>{strengths}</ul>
        <h2>需要警惕</h2><ul>{cautions}</ul>
        <h2>编辑判断</h2><blockquote>{project['verdict']}</blockquote>
        <p>下一步应完成真实安装、核心工作流、资源占用、故障恢复和卸载测试，然后再决定是否提供国内镜像。</p>
      </article>{sidebar(project)}
    </div>"""
    return page(
        project["name"], body, prefix, project["summary"],
        f"projects/{project['slug']}/", "article"
    )


def article_page(project: dict, kind: str, prefix: str) -> str:
    label = "中文评测" if kind == "review" else "使用教程"
    content = (CONTENT / project["slug"] / f"{kind}.md").read_text(encoding="utf-8")
    body = f"""{project_hero(project, kind, prefix)}
    <div class="shell content-layout"><article class="prose">{markdown(content)}</article>{sidebar(project)}</div>"""
    return page(
        f"{project['name']} {label}", body, prefix, project["summary"],
        f"projects/{project['slug']}/{kind}/", "article"
    )


def downloads(project: dict, prefix: str) -> str:
    mirror_status = "暂未开放：等待许可证复核、文件获取、SHA-256计算和安全扫描完成。"
    body = f"""{project_hero(project, "downloads", prefix)}
    <div class="shell content-layout">
      <article class="prose">
        <h2>版本记录</h2>
        <div class="download-box"><h3>{project['name']} · {project['version']}</h3>
          <p>上游仓库：<a href="{project['github']}">{project['repo']}</a></p>
          <p>许可证记录：{project['license']}</p>
          <a class="button" href="{project['github']}/releases">前往官方 Release ↗</a>
        </div>
        <h2>国内镜像</h2><div class="notice">{mirror_status}</div>
        <h2>安全校验</h2>
        <p>本站不会在没有来源记录和校验值的情况下发布安装包。未来每个文件必须记录来源URL、版本、大小、SHA-256、扫描时间和许可证。</p>
        <div class="checksum">SHA-256：等待镜像文件确定后生成</div>
        <h2>下载原则</h2>
        <ul><li>优先推荐官方应用商店、包管理器或官方Release。</li><li>本站镜像保持原始文件，不重新打包。</li><li>本站自行编译的版本必须明确标记，不能冒充官方构建。</li></ul>
      </article>{sidebar(project)}
    </div>"""
    return page(
        f"{project['name']} 版本与下载", body, prefix, project["summary"],
        f"projects/{project['slug']}/downloads/", "article"
    )


def home(projects: list[dict]) -> str:
    cards = "".join(project_card(project) for project in projects[:6])
    body = f"""
    <section class="hero shell">
      <div><p class="eyebrow">OPEN SOURCE, ACTUALLY REVIEWED</p>
      <h1>发现开源，<br><span class="highlight">不止看 Star。</span></h1>
      <p class="lede">中文评测、全中文教程、版本记录和安全下载信息。我们先替你读懂项目，再用真实操作验证它是否值得长期使用。</p>
      <div class="search"><span>⌕</span><input id="siteSearch" placeholder="搜索项目、用途或替代软件…"><span class="mono">⌘ K</span></div></div>
      <div class="radar"><span class="radar-dot"></span><div class="radar-core">8 PROJECTS<br>SELECTED</div></div>
    </section>
    <section class="strip"><div class="shell strip-inner">
      <div class="stat"><strong>8</strong><span>首批项目</span></div><div class="stat"><strong>8</strong><span>垂直领域</span></div>
      <div class="stat"><strong>16</strong><span>中文内容</span></div><div class="stat"><strong>0</strong><span>未审镜像</span></div>
    </div></section>
    <section class="section shell"><div class="section-head"><div><p class="eyebrow">EDITOR'S SELECTION</p><h2>当前精选</h2></div>
    <p id="resultCount">浏览首批高关注项目。Star用于发现，不作为最终推荐结论。</p></div>
    <div class="project-grid">{cards}</div><p style="margin-top:35px"><a class="button" href="projects/index.html">查看全部8个项目 →</a></p></section>
    <section class="workflow section"><div class="shell"><div class="section-head"><div><p class="eyebrow">OUR WORKFLOW</p><h2>一个项目，四层内容</h2></div></div>
    <div class="steps"><div class="step"><b>01</b><h3>项目初筛</h3><p>维护状态、许可证、平台和用户价值。</p></div>
    <div class="step"><b>02</b><h3>中文评测</h3><p>优势、缺点、适合人群和替代关系。</p></div>
    <div class="step"><b>03</b><h3>使用教程</h3><p>从安装到完成第一个真实工作流。</p></div>
    <div class="step"><b>04</b><h3>可信下载</h3><p>来源、版本、许可证、校验和安全扫描。</p></div></div></div></section>"""
    return page("首页", body, canonical_path="")


def project_index(projects: list[dict], prefix: str = "../") -> str:
    categories = [("all", "全部")] + [(p["category_slug"], p["category"]) for p in projects]
    seen = set()
    filters = []
    for slug, label in categories:
        if slug not in seen:
            filters.append(f'<button class="{"active" if slug == "all" else ""}" data-filter="{slug}">{label}</button>')
            seen.add(slug)
    cards = "".join(project_card(project, prefix) for project in projects)
    body = f"""<section class="page-hero"><div class="shell"><div class="breadcrumbs"><a href="{prefix}index.html">首页</a> / 项目库</div>
    <h1 style="font-size:55px;margin:0;letter-spacing:-.06em">开源项目库</h1><p class="lede">8个领域的高关注项目，所有内容均标注验证状态。</p>
    <div class="search"><span>⌕</span><input id="siteSearch" placeholder="搜索名称、用途、平台…"></div></div></section>
    <section class="section shell"><div class="filters">{''.join(filters)}</div><p id="resultCount">浏览全部精选项目</p>
    <div class="project-grid">{cards}</div></section>"""
    return page("项目库", body, prefix, "浏览开源雷达收录的高关注开源项目。", "projects/")


def categories(projects: list[dict], prefix: str = "../") -> str:
    cards = "".join(
        f"""<a class="project-card" href="{prefix}projects/{p['slug']}/index.html">
        <div class="project-icon" style="--accent:{p['accent']}">{p['letter']}</div>
        <div class="category">{p['category_slug'].upper()}</div><h3>{p['category']}</h3>
        <p>代表项目：{p['name']} · ★ {p['stars']}</p><div class="project-footer"><span>1个首批项目</span><span>浏览 →</span></div></a>"""
        for p in projects
    )
    body = f"""<section class="page-hero"><div class="shell"><div class="breadcrumbs"><a href="{prefix}index.html">首页</a> / 分类</div>
    <h1 style="font-size:55px;margin:0;letter-spacing:-.06em">项目分类</h1><p class="lede">首版每个领域选择一个代表项目，后续以同类横向比较扩展。</p></div></section>
    <section class="section shell"><div class="project-grid">{cards}</div></section>"""
    return page("项目分类", body, prefix, "按用途浏览开源软件与工具。", "categories/")


def static_info(
    title: str, heading: str, content: str, prefix: str = "../", canonical_path: str = ""
) -> str:
    body = f"""<section class="page-hero"><div class="shell"><div class="breadcrumbs"><a href="{prefix}index.html">首页</a> / {title}</div>
    <h1 style="font-size:55px;margin:0;letter-spacing:-.06em">{heading}</h1></div></section>
    <div class="shell content-layout"><article class="prose">{markdown(content)}</article></div>"""
    return page(title, body, prefix, canonical_path=canonical_path, page_type="article")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sitemap(projects: list[dict]) -> str:
    paths = ["", "projects/", "categories/", "methodology/", "about/", "legal/"]
    for project in projects:
        base = f"projects/{project['slug']}/"
        paths.extend([base, base + "review/", base + "tutorial/", base + "downloads/"])
    entries = "\n".join(
        f"""  <url><loc>{xml_escape(absolute(path))}</loc><lastmod>{TODAY}</lastmod></url>"""
        for path in paths
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""


def rss(projects: list[dict]) -> str:
    items = []
    for project in projects:
        link = absolute(f"projects/{project['slug']}/review/")
        items.append(f"""    <item>
      <title>{xml_escape(project['name'])} 中文初评</title>
      <link>{xml_escape(link)}</link>
      <guid>{xml_escape(link)}</guid>
      <pubDate>Thu, 02 Jul 2026 00:00:00 +0800</pubDate>
      <description>{xml_escape(project['summary'])}</description>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
    <title>{xml_escape(SITE['name'])}</title>
    <link>{xml_escape(absolute())}</link>
    <description>{xml_escape(SITE['description'])}</description>
    <language>zh-cn</language>
    <lastBuildDate>Thu, 02 Jul 2026 00:00:00 +0800</lastBuildDate>
{chr(10).join(items)}
  </channel></rss>
"""


def build() -> None:
    projects = load_projects()
    ensure_content(projects)
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    shutil.copy2(STATIC / "style.css", DIST / "assets" / "style.css")
    shutil.copy2(STATIC / "site.js", DIST / "assets" / "site.js")
    shutil.copy2(STATIC / "favicon.svg", DIST / "assets" / "favicon.svg")
    shutil.copy2(STATIC / "social-card.svg", DIST / "assets" / "social-card.svg")

    write(DIST / "index.html", home(projects))
    write(DIST / "projects" / "index.html", project_index(projects))
    write(DIST / "categories" / "index.html", categories(projects))

    for project in projects:
        base = DIST / "projects" / project["slug"]
        write(base / "index.html", overview(project, "../../"))
        write(base / "review" / "index.html", article_page(project, "review", "../../../"))
        write(base / "tutorial" / "index.html", article_page(project, "tutorial", "../../../"))
        write(base / "downloads" / "index.html", downloads(project, "../../../"))

    method = """# 评测方法

## 当前内容状态

第一版内容由AI根据GitHub项目页、官方文档、许可证和公开Release生成。它是选题与结构草稿，不等同于人工完成的真实评测。

## 状态标签

- **AI初评**：完成公开资料研究，尚未完成真实设备测试。
- **人工验证中**：已开始安装和核心功能测试。
- **人工已验证**：记录了环境、步骤、结果、缺点和恢复方式。
- **需要复测**：上游重大更新后，旧结论可能失效。

## 评分维度

1. 上手难度：普通用户完成首次使用的难度。
2. 功能完整：项目对目标问题的覆盖程度。
3. 隐私控制：用户对数据、网络和部署的控制能力。
4. 维护活跃：基于公开更新与社区活动的初步判断。

## 镜像发布门槛

必须完成许可证复核、官方来源确认、原文件保留、SHA-256计算、安全扫描和下架渠道，才允许显示国内镜像下载按钮。
"""
    about = """# 关于开源雷达

开源雷达希望帮助中文用户发现真正有用的开源项目，并降低从“看到项目”到“完成第一次使用”的距离。

## 我们提供什么

- 中文项目评测
- 全中文Markdown教程
- 版本与许可证记录
- 官方下载和合规国内镜像
- SHA-256与安全检查信息

## 我们不做什么

- 不把GitHub Star当作唯一质量指标。
- 不复制README伪装成原创评测。
- 不在未经验证时宣称“已实测”。
- 不提供来源不明或许可证不清晰的安装包。

本站当前是第一版产品系统，用于验证内容结构、工作流和后续运营方式。
"""
    legal = f"""# 法律、隐私与内容政策

> 本页面是网站首版运营政策，不构成针对任何个人或项目的法律意见。最后更新：{TODAY}。

## 内容与免责声明

本站提供开源项目介绍、中文评测、使用教程、版本记录和下载来源信息。内容仅用于一般信息与学习参考，不保证软件适合特定用途，也不承诺项目持续可用、没有缺陷或绝对安全。

AI生成的初评会明确标注，不能替代人工测试。用户安装、部署或运行第三方软件前，应自行核对项目官方文档、许可证和安全公告，并为重要数据建立备份。

## 商标与项目归属

项目名称、Logo、商标、源代码和安装包归各自权利人所有。本站不是这些项目的官方网站，除非页面另有明确说明，本站与项目维护者不存在隶属或授权关系。

## 许可证与转载

公开可见不等于允许重新分发。本站在提供国内镜像前，会逐项检查开源许可证、版权声明、NOTICE、对应源代码义务及项目的额外分发规则。许可证不明确或禁止转载的项目只提供官方链接。

## 镜像与文件安全政策

- 只从项目官方网站、官方代码仓库或官方Release获取文件。
- 原始安装包原则上不重新打包。
- 记录版本、来源地址、文件大小、SHA-256和获取日期。
- 完成安全扫描后才开放镜像链接。
- 自行构建的文件必须标记为“本站构建”，不能冒充官方版本。
- 发现来源、许可证或安全问题时，可以立即停止分发。

镜像仅改善访问体验，不代表本站对第三方软件提供担保。

## 隐私政策

本站当前不要求注册账号，也不主动收集敏感个人信息。部署访问统计后，可能处理页面访问、设备类型、来源页面、粗略地区和技术错误信息，用于改进内容与性能。

本站不会出售个人信息。第三方托管、统计、CDN和外部链接可能按其自身政策处理数据。正式启用任何统计或广告服务前，本页会补充服务商、Cookie及退出方式。

## 广告与赞助

广告、联盟链接和赞助评测必须明确标记。商业合作不会自动获得正面评价，也不能删除真实缺点。赞助内容与编辑结论应保持可识别的边界。

## 版权投诉、安全报告与下架

如果你是项目维护者或权利人，认为本站内容、商标、截图、镜像或许可证处理存在问题，请通过 **{SITE['contact_email']}** 联系，并提供项目地址、权利说明、涉及页面和期望处理方式。

对于可信的恶意文件、供应链风险或许可证问题，本站将优先暂停下载，再进行核查。

## 外部链接

本站包含GitHub、项目官网和其他第三方链接。外部网站的内容、可用性和隐私实践由其自身负责。
"""
    write(
        DIST / "methodology" / "index.html",
        static_info("评测方法", "我们如何评价一个项目", method, canonical_path="methodology/")
    )
    write(
        DIST / "about" / "index.html",
        static_info("关于", "关于开源雷达", about, canonical_path="about/")
    )
    write(
        DIST / "legal" / "index.html",
        static_info("法律与政策", "法律、隐私与内容政策", legal, canonical_path="legal/")
    )

    search_data = [
        {"name": p["name"], "category": p["category"], "summary": p["summary"], "url": f"projects/{p['slug']}/index.html"}
        for p in projects
    ]
    write(DIST / "assets" / "search-index.json", json.dumps(search_data, ensure_ascii=False, indent=2))
    write(DIST / "sitemap.xml", sitemap(projects))
    write(DIST / "rss.xml", rss(projects))
    write(
        DIST / "robots.txt",
        f"User-agent: *\nAllow: /\n\nSitemap: {absolute('sitemap.xml')}\n"
    )
    not_found = """<section class="hero shell"><div><p class="eyebrow">ERROR 404</p>
    <h1>没有找到<br><span class="highlight">这个页面。</span></h1>
    <p class="lede">链接可能已经更改，或者项目尚未被收录。</p>
    <a class="button" href="index.html">返回首页 →</a></div>
    <div class="radar"><div class="radar-core">SIGNAL<br>NOT FOUND</div></div></section>"""
    write(
        DIST / "404.html",
        page("页面不存在", not_found, canonical_path="404.html", robots="noindex,follow")
    )
    write(DIST / "_redirects", "/404 /404.html 404\n/* /404.html 404\n")
    headers = """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'

/assets/*
  Cache-Control: public, max-age=31536000, immutable
"""
    write(DIST / "_headers", headers)
    print(f"Built {len(projects)} projects and {len(list(DIST.rglob('*.html')))} HTML pages in {DIST}")


if __name__ == "__main__":
    build()
