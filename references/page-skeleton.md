# 页面骨架 · 可直接复制的生成器代码

> 目标：任何新数学页都从这套骨架起手，**不再手写 HTML**。改的只是内容数据。
> 基座：`<工作区>/疑难档案/生成.py` 提供 `TEMPLATE`（已验证的自包含 head）、`EXTRAS_CSS`、`TOC_JS`、`esc_attr()`。

---

## 1. 目录约定

```
<工作区>/
  katex/                     # katex.min.css / katex.min.js / auto-render.min.js / fonts/
  疑难档案/生成.py            # 基座：TEMPLATE + EXTRAS_CSS + TOC_JS + esc_attr
  疑难档案/档案数据.json       # 题目/概念档案（C-xxx / 卷名-Q-xxx）
  公式备忘/生成.py + 公式数据.json   # 公式库（FM-xxx / FM-xxx-n）
  微分通关/生成.py            # 专题讲解（T-xx）
  <专题>/生成.py              # 新专题照此建
```

生成器只做三件事：**读数据 → 拼 body → 套 TEMPLATE 的 head/tail**。

---

## 2. 最小生成器（照抄改名即可）

```python
# -*- coding: utf-8 -*-
import os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

spec = importlib.util.spec_from_file_location("base", os.path.join(ROOT, "疑难档案", "生成.py"))
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
esc = base.esc_attr
TEMPLATE = base.TEMPLATE

EXTRAS_CSS = base.EXTRAS_CSS + """
.q{background:#f7f9fb;border:1px solid #dbe3ec;border-radius:10px;padding:11px 15px;margin:12px 0}
.formula{background:#f3f8f4;border:1px solid #cfe3cf;border-left:5px solid #1b7a3d;border-radius:10px;padding:10px 14px;margin:10px 0}
.warn{background:#fff4f4;border:1px solid #eebbb4;border-left:5px solid #c0392b;border-radius:10px;padding:10px 14px;margin:10px 0}
.fig{background:#fbfdff;border:1px solid #d9e3ee;border-radius:10px;padding:8px 10px;margin:12px 0;text-align:center}
.fig svg{display:block;margin:0 auto!important;width:100%;max-width:660px;height:auto;background:transparent!important;border:0!important;border-radius:0!important}
.fig .fc{font-size:12.8px;color:#4a5b6b;margin-top:6px;line-height:1.75;text-align:left}
"""

body = ['<h1 id="top">标题</h1>', '<p class="cap">副标题</p>']
body.append('<div class="q" id="T-01"><h3>T-01 标题</h3>'
            + '<div class="idea"><span class="lab">直觉</span>…</div>'
            + '<div class="formula"><b>公式：</b>$…$</div>'
            + '</div>')

def main():
    raw = open(TEMPLATE, "rb").read()
    while raw[:3] == b"\xef\xbb\xbf":          # ← 字节级剥 BOM，P3
        raw = raw[3:]
    tpl = raw.decode("utf-8")
    head = tpl[:tpl.index("<body")]
    tail = tpl[tpl.rfind("<script>"):]         # tail 里已含 </html>，不要再追加
    head = head.replace("</head>", "<style>%s</style>\n</head>" % EXTRAS_CSS, 1)

    toc = ['<div class="toc-h">目录 · 实时定位</div>', '<a href="#top">▲ 顶部</a>', '<div class="toc-list">']
    toc.append('<a href="#T-01" data-id="T-01">T-01 标题</a>')
    toc.append('</div>')

    lay = ('<div id="layout">\n<nav id="toc" aria-label="目录">' + "\n".join(toc) + '</nav>\n'
           '<div id="main">\n' + "\n".join(body) + '\n</div>\n</div>\n'
           '<script>' + base.TOC_JS + '</script>')

    html = head + "\n<body>\n" + lay + "\n" + tail
    if not html.rstrip().endswith("</html>"):
        html = html.rstrip() + "\n</html>\n"
    out = os.path.join(ROOT, "输出.html")
    open(out, "wb").write(b"\xef\xbb\xbf" + html.encode("utf-8"))
    print("[out]", out, len(html.encode("utf-8")))

if __name__ == "__main__":
    main()
```

---

## 3. 必须保留的 CSS 复位（P1）

```css
/* fix-radical：中和页面全局 svg{} 规则对 KaTeX 内部根号 svg 的影响 */
.katex svg{margin:0!important;padding:0!important;background:transparent!important;
           border:0!important;border-radius:0!important;box-shadow:none!important}
```

**不要写 `display:inline`** —— 会让分母里的 `√` 变成 `𝜑`。

---

## 4. 目录 scroll-spy（TOC_JS 关键逻辑，已内置在基座）

```js
var items = [].slice.call(document.querySelectorAll('#main .q[id]'));
// 两级目录（条目 + 子公式）时改成：
// '#main .q[id], #main .formula .stmt[id]'
function onScroll(){
  var line = 140, cur = items[0];
  for (var i = 0; i < items.length; i++){
    var r = items[i].getBoundingClientRect();
    if (r.top <= line) cur = items[i]; else break;
  }
  setActive(cur);
}
window.__tocRefresh = onScroll;   // ← 供自动化核对：伪造位置后手动触发
```

配套：`html{scroll-behavior:smooth}`、`#toc{position:sticky;top:14px}`、`.q[id]{scroll-margin-top:96px}`、
窄屏 `@media(max-width:1000px){#toc{position:static} #toc .toc-list{columns:2}}`。

---

## 5. 内容积木（四件套的落地形态）

| 积木 | HTML | 用途 |
|---|---|---|
| 直觉 | `<div class="idea"><span class="lab">直觉</span>…</div>` | R1-① |
| 公式 | `<div class="formula"><b>公式：</b>$…$</div>` | 公式本体 / 形象推导 |
| 微例 | `<div class="formula"><b>微例：</b>…</div>` | R1-② 当场算一遍 |
| 何时用 | `<div class="step"><span class="tag step">何时用</span>…</div>` | R1-③ |
| 连接 | `<div class="step"><span class="tag t3">连接</span>…</div>` | R1-④ |
| 排雷 | `<div class="warn"><span class="fl">排雷</span>…</div>` | 易错点 |
| 图 | `<div class="fig">{svg}<div class="fc">一句话读图：…</div></div>` | R6 |
| 子编号 | `<div class="stmt" id="FM-001-3"><span class="sidbadge">FM-001-3</span>…</div>` | 公式库 |

**每张图都要有"一句话读图"**——图不是装饰，是论证的一环。

---

## 6. 图的画法约定

- `viewBox` 宽取 680~760，`<text>` 用 `font-family="Cambria,Georgia,serif"` 走数学斜体，`font-style="italic"` 标变量。
- 每个标注都要有**归属**：要么贴线，要么加引线；两条竖线太近时改成"尺寸线"（横引线 + 竖线 + 文字）。
- 曲线用**真实采样**（Python 算点喂给 `<polyline points>`），不要手绘 svg path 假装。
- 图内不塞长句说明，说明放图下的 `.fc`。
