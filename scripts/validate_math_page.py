#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学页五关校验（math-lecture-standard / 步骤 3）

用法：
    python validate_math_page.py 页面.html                # 静态四关
    python validate_math_page.py 页面.html --headless     # 追加无头渲染关
    python validate_math_page.py 页面.html --expect 226   # 断言公式节点数

退出码：0 全过 / 1 有问题。任何一项 FAIL 都不许交付。
"""
import os
import re
import sys
import shutil
import tempfile
import subprocess
from html.parser import HTMLParser

VOID = {"br", "hr", "img", "meta", "link", "input", "source", "area", "base",
        "col", "embed", "param", "track", "wbr"}

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


class TagCheck(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.err = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.err.append(("stray-end", tag, self.getpos()))
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.err.append(("implicit-close", self.stack.pop(), self.getpos()))
            if self.stack:
                self.stack.pop()
        else:
            self.err.append(("stray-end", tag, self.getpos()))


def static_checks(path):
    raw = open(path, "rb").read()
    bombs = 0
    while raw.startswith(b"\xef\xbb\xbf"):
        bombs += 1
        raw = raw[3:]
    txt = raw.decode("utf-8", errors="replace")

    p = TagCheck()
    p.feed(txt)

    i = txt.find("<body")
    body = txt[i:txt.rfind("</body>")] if i >= 0 else txt
    body = re.sub(r"<script[\s\S]*?</script>", "", body)
    body = re.sub(r"<style[\s\S]*?</style>", "", body)
    segs = re.findall(r"\$[^$\n]{1,400}\$", body)
    bare = [s for s in segs if "<" in s or ">" in s]

    toc = re.findall(r'<a href="#([\w\-]+)"', txt)
    ids = set(re.findall(r'id="([\w\-]+)"', txt))
    missing = sorted({t for t in toc if t not in ids and t != "top"})

    rows = [
        ("① BOM", bombs == 1, "%d 个（应为 1）" % bombs),
        ("② 标签", len(p.err) == 0 and len(p.stack) == 0,
         "err=%d 残留栈=%d %s" % (len(p.err), len(p.stack), p.stack[:5])),
        ("③ 公式字符", len(bare) == 0, "裸尖括号片段=%d %s" % (len(bare), bare[:2])),
        ("③' 替换符", "\ufffd" not in txt, "U+FFFD=%d" % txt.count("\ufffd")),
        ("④ 目录锚点", len(missing) == 0, "toc=%d 缺失=%s" % (len(set(toc)), missing[:5])),
    ]
    for name, ok, detail in rows:
        print("%-10s %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    print("%-10s %s  %d" % ("$..$ 片段", "info", len(segs)))
    return all(ok for _, ok, _ in rows)


def headless_check(path, expect=None):
    exe = next((e for e in EDGE_CANDIDATES if os.path.exists(e)), None)
    if not exe:
        print("%-10s %s  %s" % ("⑤ 渲染", "SKIP", "未找到 Edge/Chrome"))
        return True

    tmp = tempfile.mkdtemp(prefix="mathval_")
    # 纯 ASCII 路径：Edge 对中文路径的 file:// 会 ERR_FILE_NOT_FOUND
    dst = os.path.join(tmp, "page.html")
    shutil.copyfile(path, dst)
    url = "file:///" + dst.replace("\\", "/")
    prof = os.path.join(tmp, "prof").replace("\\", "/")

    out = subprocess.run(
        [exe, "--headless=new", "--disable-gpu", "--virtual-time-budget=12000",
         "--user-data-dir=" + prof, "--dump-dom", url],
        capture_output=True, timeout=180,
    )
    dom = out.stdout.decode("utf-8", errors="replace")
    n_katex = dom.count('class="katex"')
    n_err = len(re.findall(r'class="katex-error"', dom))

    ok = n_katex > 0 and n_err == 0
    detail = "katex 节点=%d 渲染错误=%d" % (n_katex, n_err)
    if expect is not None and n_katex != expect:
        ok = False
        detail += "（期望 %d）" % expect
    print("%-10s %s  %s" % ("⑤ 渲染", "PASS" if ok else "FAIL", detail))
    shutil.rmtree(tmp, ignore_errors=True)
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    path = args[0]
    expect = None
    if "--expect" in sys.argv:
        expect = int(sys.argv[sys.argv.index("--expect") + 1])
        args = [a for a in args if a != str(expect)]
        path = args[0]

    print("file:", os.path.basename(path), "|", os.path.getsize(path), "bytes")
    ok = static_checks(path)
    if "--headless" in sys.argv:
        ok = headless_check(path, expect) and ok
    print("=" * 56)
    print("RESULT:", "ALL PASS" if ok else "HAS FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
