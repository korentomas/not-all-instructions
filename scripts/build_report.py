"""Render REPORT.md -> REPORT.html in the dark-editorial report style
(matching the PowerBench reports: gold accent, serif headers, panels).

    python scripts/build_report.py
"""
from pathlib import Path
import base64
import re
import markdown

ROOT = Path(__file__).resolve().parents[1]
md_text = (ROOT / "REPORT.md").read_text()

lines = md_text.splitlines()
body_md = "\n".join(lines[1:]).strip() if lines and lines[0].startswith("# ") else md_text

md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists"],
                       extension_configs={"toc": {"permalink": False}})
body_html = md.convert(body_md)
toc_html = md.toc


def _inline_images(html: str) -> str:
    """Base64-inline local PNGs so the report is a single self-contained file."""
    def repl(m):
        p = ROOT / m.group(1)
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            return f'src="data:image/png;base64,{b64}"'
        return m.group(0)
    return re.sub(r'src="([^"]+\.png)"', repl, html)


body_html = _inline_images(body_html)

CSS = """
:root { --ground:#181B24; --panel:#1E2230; --text:#E9E6DC; --muted:#9A9789;
  --accent:#C9A24B; --teal:#57B0A8; --clay:#C0503C; --rule:#2C3140; --line:#232838; }
* { box-sizing:border-box; }
body { margin:0; background:var(--ground); color:var(--text);
  font-family:-apple-system,system-ui,"Segoe UI",sans-serif; line-height:1.6; -webkit-font-smoothing:antialiased; }
.mono { font-family:ui-monospace,"SF Mono",Menlo,monospace; }
.wrap { max-width:860px; margin:0 auto; padding:0 28px 96px; }
.masthead { padding:64px 0 36px; border-bottom:1px solid var(--rule); }
.eyebrow { font-size:12px; letter-spacing:.22em; text-transform:uppercase; color:var(--accent); margin:0 0 22px; }
h1 { font-family:"Hoefler Text",Palatino,Georgia,serif; font-weight:600; font-size:clamp(30px,5vw,46px);
  line-height:1.07; letter-spacing:-.01em; margin:0 0 18px; }
h1 em { font-style:italic; color:var(--accent); }
.dek { font-size:17px; color:var(--muted); max-width:62ch; margin:0; }
.meta { display:flex; gap:24px; flex-wrap:wrap; margin-top:28px; font-size:12.5px; color:var(--muted); }
.meta b { color:var(--text); font-weight:600; }
.toc { margin:40px 0 8px; padding:22px 26px; background:var(--panel); border:1px solid var(--rule); border-radius:3px; }
.toc-title { font-size:11px; letter-spacing:.18em; text-transform:uppercase; color:var(--accent); margin:0 0 12px; }
.toc ul { list-style:none; margin:0; padding:0; } .toc ul ul { padding-left:18px; margin-top:4px; }
.toc li { margin:4px 0; font-size:13.5px; }
.toc a { color:var(--muted); text-decoration:none; } .toc a:hover { color:var(--text); }
.content { padding-top:8px; }
.content h2 { font-family:"Hoefler Text",Palatino,Georgia,serif; font-weight:600; font-size:27px;
  letter-spacing:-.01em; color:var(--text); margin:56px 0 6px; padding-top:30px; border-top:1px solid var(--rule); }
.content h3 { font-size:18px; font-weight:600; color:var(--accent); margin:34px 0 4px; }
.content h4 { font-size:14px; font-weight:600; color:var(--text); margin:24px 0 2px; }
.content p { font-size:15.5px; color:#D7D3C8; margin:14px 0; max-width:70ch; }
.content a { color:var(--accent); text-decoration:none; border-bottom:1px solid rgba(201,162,75,.3); }
.content a:hover { border-bottom-color:var(--accent); }
.content strong { color:var(--text); font-weight:600; }
.content em { color:#E9E6DC; }
.content ul, .content ol { max-width:70ch; padding-left:22px; }
.content li { margin:7px 0; font-size:15px; color:#D7D3C8; }
.content blockquote { border-left:2px solid var(--accent); margin:22px 0; padding:6px 0 6px 20px;
  color:var(--muted); font-size:14.5px; }
.content blockquote p { color:var(--muted); }
.content code { font-family:ui-monospace,Menlo,monospace; color:var(--text); background:#11131a;
  padding:.1em .35em; border-radius:2px; font-size:.88em; }
.content pre { background:#11131a; border:1px solid var(--rule); border-radius:3px; padding:14px 16px;
  overflow:auto; font-size:12.5px; } .content pre code { background:none; padding:0; }
.content hr { border:none; border-top:1px solid var(--rule); margin:44px 0; }
.content img { display:block; max-width:100%; height:auto; margin:28px auto 6px;
  border:1px solid var(--rule); border-radius:3px; background:#181B24; }
.content .figcap { text-align:center; color:var(--muted); font-size:12.5px;
  margin:0 auto 10px; max-width:66ch; }
.content table { width:100%; border-collapse:collapse; margin:20px 0; font-size:13px;
  font-variant-numeric:tabular-nums; }
.content th { text-align:left; color:var(--muted); font-weight:600; padding:9px 12px;
  border-bottom:1px solid var(--rule); font-size:11.5px; letter-spacing:.04em; text-transform:uppercase; }
.content td { padding:9px 12px; border-bottom:1px solid var(--line); color:#D7D3C8; vertical-align:top; }
.content tr:hover td { background:#1c2030; }
footer { margin-top:56px; padding-top:20px; border-top:1px solid var(--rule); font-size:11.5px; color:var(--muted); }
@media (prefers-reduced-motion:reduce) { * { transition:none !important; } }
"""

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Not All Instructions Are Forgotten Equal — report</title>
<style>{CSS}</style></head><body>
<div class="wrap">
  <header class="masthead">
    <p class="eyebrow">Context Rot · 55 JAIIO / ASAID 2026</p>
    <h1>Not All Instructions Are<br><em>Forgotten Equal</em></h1>
    <p class="dek">Per-instruction retention in long LLM coding conversations: which
      user-stated preferences a model keeps, which it ignores, and which one it follows
      <em>less</em> once you ask.</p>
    <div class="meta">
      <div><b>244</b> observations · <b>5</b> models</div>
      <div><b>12</b> decision types · <b>3</b> codebases</div>
      <div>Bayesian ordered-logit · deterministic checkers</div>
    </div>
  </header>

  <nav class="toc">
    <p class="toc-title">Contents</p>
    {toc_html}
  </nav>

  <main class="content">
    {body_html}
  </main>

  <footer>Not All Instructions Are Forgotten Equal · generated from REPORT.md by scripts/build_report.py</footer>
</div>
</body></html>
"""

out = ROOT / "REPORT.html"
out.write_text(HTML)
print(f"wrote {out} ({len(HTML):,} bytes)")
