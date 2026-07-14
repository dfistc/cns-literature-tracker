from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "literature.json"
OUTPUT_PATH = ROOT / "文献库网页.html"
PAGES_OUTPUT_PATH = ROOT / "site" / "index.html"


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CNS 合成生物学与蛋白降解文献库</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f2;
      --panel: #ffffff;
      --ink: #15201b;
      --muted: #546157;
      --line: #d7dccf;
      --green: #255237;
      --soft: #e3efe4;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Microsoft YaHei", "Noto Sans SC", Arial, sans-serif;
    }}
    header {{
      background: #eef2e6;
      border-bottom: 1px solid var(--line);
      padding: 28px 24px 22px;
    }}
    .wrap {{ max-width: 1180px; margin: 0 auto; }}
    .top {{
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: end;
    }}
    .eyebrow {{
      color: #5b6f55;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: .16em;
      text-transform: uppercase;
    }}
    h1 {{ font-size: clamp(30px, 5vw, 52px); line-height: 1.12; margin: 10px 0 12px; }}
    .intro {{ color: var(--muted); line-height: 1.75; max-width: 760px; margin: 0; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(2, minmax(120px, 1fr));
      gap: 10px;
      min-width: 300px;
      background: rgba(255,255,255,.75);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .metric:last-child {{ grid-column: 1 / -1; }}
    .metric small {{ display: block; color: #6a766c; font-size: 12px; font-weight: 700; letter-spacing: .1em; }}
    .metric strong {{ display: block; margin-top: 4px; font-size: 18px; }}
    .filters {{
      display: grid;
      grid-template-columns: 1.4fr 1fr 1fr 1fr;
      gap: 12px;
      margin-top: 24px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    label {{ display: grid; gap: 6px; }}
    label span {{ color: #5c675f; font-size: 12px; font-weight: 800; letter-spacing: .1em; }}
    input, select {{
      width: 100%;
      min-height: 42px;
      border: 1px solid #cbd3c4;
      border-radius: 6px;
      background: #fbfcf8;
      color: var(--ink);
      font-size: 15px;
      padding: 8px 10px;
    }}
    main {{ padding: 22px 24px 36px; }}
    .note {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      color: var(--muted);
      font-size: 14px;
      margin-bottom: 14px;
    }}
    button {{
      border: 1px solid #315c3d;
      border-radius: 6px;
      background: #fff;
      color: #21472e;
      cursor: pointer;
      font-weight: 700;
      min-height: 34px;
      padding: 6px 12px;
      white-space: nowrap;
    }}
    .list {{ display: grid; gap: 14px; }}
    article {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgba(30,40,34,.05);
      padding: 18px;
    }}
    .article-head {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
    }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .chip {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border: 1px solid #c7dcc9;
      border-radius: 999px;
      background: var(--soft);
      color: var(--green);
      font-size: 13px;
      font-weight: 800;
      padding: 3px 9px;
    }}
    .chip.muted {{ background: #f0f2ea; border-color: #dde2d4; color: #59655b; }}
    h2 {{ margin: 12px 0 0; font-size: clamp(18px, 2.3vw, 24px); line-height: 1.35; }}
    .title-zh {{ color: #405047; font-size: 17px; font-weight: 700; line-height: 1.55; margin: 7px 0 0; }}
    .links {{ display: flex; flex-wrap: wrap; gap: 8px; flex: 0 0 auto; }}
    .links a {{
      border: 1px solid #315c3d;
      border-radius: 6px;
      color: #21472e;
      font-weight: 800;
      min-height: 34px;
      padding: 6px 12px;
      text-decoration: none;
    }}
    dl {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      border-top: 1px solid #e1e5dc;
      margin: 16px 0 0;
      padding-top: 14px;
    }}
    dt, h3 {{ color: #69746a; font-size: 12px; font-weight: 900; letter-spacing: .1em; margin: 0; }}
    dd {{ margin: 5px 0 0; color: #253028; line-height: 1.55; overflow-wrap: anywhere; }}
    .body {{
      display: grid;
      grid-template-columns: minmax(0, .85fr) minmax(0, 1.35fr);
      gap: 18px;
      margin-top: 16px;
    }}
    .body p {{ color: #3f4b43; line-height: 1.78; margin: 6px 0 0; }}
    .empty {{
      border: 1px dashed #bfc8b8;
      border-radius: 8px;
      color: #59655c;
      padding: 32px;
      text-align: center;
    }}
    @media (max-width: 820px) {{
      .top, .filters, dl, .body {{ grid-template-columns: 1fr; }}
      .metrics {{ min-width: 0; }}
      .article-head, .note {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <div class="top">
        <div>
          <div class="eyebrow">CNS literature tracker</div>
          <h1>合成生物学与蛋白降解文献库</h1>
          <p class="intro">自动搜集 2020 年以来 CNS 正刊及 Cell/Nature/Science 系列子刊中，和合成生物学、靶向蛋白降解、溶酶体或蛋白酶体相关的文献。</p>
        </div>
        <div class="metrics">
          <div class="metric"><small>收录文献</small><strong id="total">0</strong></div>
          <div class="metric"><small>当前显示</small><strong id="shown">0</strong></div>
          <div class="metric"><small>更新时间</small><strong id="updated">尚未更新</strong></div>
        </div>
      </div>
      <div class="filters">
        <label><span>检索</span><input id="query" placeholder="题名、DOI、关键词" /></label>
        <label><span>主题</span><select id="category"></select></label>
        <label><span>期刊</span><select id="journal"></select></label>
        <label><span>年份</span><select id="year"></select></label>
      </div>
    </div>
  </header>
  <main>
    <div class="wrap">
      <div class="note">
        <div>数据源：{html.escape(data.get("source", ""))}。DOI 来自 PubMed ArticleId，链接指向 DOI 和 PubMed 原始记录。</div>
        <button id="reset">清除筛选</button>
      </div>
      <div class="list" id="list"></div>
    </div>
  </main>
  <script id="literature-data" type="application/json">{payload}</script>
  <script>
    const data = JSON.parse(document.getElementById("literature-data").textContent);
    const allCategory = "全部主题";
    const allJournal = "全部期刊";
    const allYear = "全部年份";
    const state = {{ category: allCategory, journal: allJournal, year: allYear, query: "" }};
    const els = {{
      total: document.getElementById("total"),
      shown: document.getElementById("shown"),
      updated: document.getElementById("updated"),
      list: document.getElementById("list"),
      query: document.getElementById("query"),
      category: document.getElementById("category"),
      journal: document.getElementById("journal"),
      year: document.getElementById("year"),
      reset: document.getElementById("reset"),
    }};
    function unique(values) {{ return Array.from(new Set(values)).filter(Boolean); }}
    function fillSelect(el, values) {{
      el.innerHTML = values.map(value => `<option value="${{escapeHtml(value)}}">${{escapeHtml(value)}}</option>`).join("");
    }}
    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, char => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }}[char]));
    }}
    function formatTime(value) {{
      if (!value) return "尚未更新";
      return new Intl.DateTimeFormat("zh-CN", {{ year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }}).format(new Date(value));
    }}
    function render() {{
      const term = state.query.trim().toLowerCase();
      const items = data.items.filter(item => {{
        const text = `${{item.title}} ${{item.titleZh || ""}} ${{item.journal}} ${{item.doi}} ${{item.summaryZh}} ${{(item.matchedTerms || []).join(" ")}}`.toLowerCase();
        return (state.category === allCategory || item.categories.includes(state.category))
          && (state.journal === allJournal || item.journal === state.journal)
          && (state.year === allYear || String(item.year) === state.year)
          && (!term || text.includes(term));
      }});
      els.shown.textContent = items.length;
      els.list.innerHTML = items.length ? items.map(renderItem).join("") : `<div class="empty">没有匹配的文献。可以放宽主题、期刊或年份筛选。</div>`;
    }}
    function renderItem(item) {{
      const chips = [...item.categories.map(name => `<span class="chip">${{escapeHtml(name)}}</span>`), `<span class="chip muted">${{item.year}}</span>`, `<span class="chip muted">${{escapeHtml(item.journal)}}</span>`].join("");
      return `<article>
        <div class="article-head">
          <div><div class="chips">${{chips}}</div><h2>${{escapeHtml(item.title)}}</h2><p class="title-zh">${{escapeHtml(item.titleZh || "中文题名待翻译")}}</p></div>
          <div class="links"><a href="${{escapeHtml(item.doiUrl)}}" target="_blank" rel="noreferrer">DOI</a><a href="${{escapeHtml(item.pubmedUrl)}}" target="_blank" rel="noreferrer">PubMed</a></div>
        </div>
        <dl>
          <div><dt>DOI</dt><dd>${{escapeHtml(item.doi)}}</dd></div>
          <div><dt>发表时间</dt><dd>${{escapeHtml(item.published || item.year)}}</dd></div>
          <div><dt>命中词</dt><dd>${{escapeHtml((item.matchedTerms || []).join(" / ") || "关键词复核")}}</dd></div>
        </dl>
        <div class="body">
          <section><h3>纳入标准</h3><p>${{escapeHtml(item.standard)}}</p></section>
          <section><h3>摘要中文翻译</h3><p>${{escapeHtml(item.summaryZh || "中文摘要待翻译")}}</p></section>
        </div>
      </article>`;
    }}
    fillSelect(els.category, [allCategory, ...unique(data.items.flatMap(item => item.categories)).sort()]);
    fillSelect(els.journal, [allJournal, ...unique(data.items.map(item => item.journal)).sort()]);
    fillSelect(els.year, [allYear, ...unique(data.items.map(item => String(item.year))).sort().reverse()]);
    els.total.textContent = data.items.length;
    els.updated.textContent = formatTime(data.updatedAt);
    els.query.addEventListener("input", event => {{ state.query = event.target.value; render(); }});
    els.category.addEventListener("change", event => {{ state.category = event.target.value; render(); }});
    els.journal.addEventListener("change", event => {{ state.journal = event.target.value; render(); }});
    els.year.addEventListener("change", event => {{ state.year = event.target.value; render(); }});
    els.reset.addEventListener("click", () => {{
      state.category = allCategory; state.journal = allJournal; state.year = allYear; state.query = "";
      els.query.value = ""; els.category.value = allCategory; els.journal.value = allJournal; els.year.value = allYear;
      render();
    }});
    render();
  </script>
</body>
</html>
"""
    OUTPUT_PATH.write_text(document, encoding="utf-8")
    PAGES_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAGES_OUTPUT_PATH.write_text(document, encoding="utf-8")
    (PAGES_OUTPUT_PATH.parent / ".nojekyll").write_text("", encoding="ascii")
    print(OUTPUT_PATH)
    print(PAGES_OUTPUT_PATH)


if __name__ == "__main__":
    main()
