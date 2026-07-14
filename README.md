# CNS 合成生物学与蛋白降解文献库

本项目自动收集 2020 年以来 CNS 正刊及 Cell、Nature、Science 系列子刊中，与合成生物学、靶向蛋白降解、溶酶体或蛋白酶体相关的 PubMed 文献。

网站为静态页面，展示英文题名、中文题名、DOI、PubMed 链接、纳入标准和 PubMed 摘要中文翻译。DOI 与网址只采用 PubMed 返回的记录，不由程序猜测生成。

## 自动更新

GitHub Actions 每天北京时间 08:00 自动执行：

1. 从 PubMed E-utilities 检索和核验文献。
2. 只翻译新增或原文发生变化的英文题名与摘要。
3. 生成 `site/index.html` 和本地版 `文献库网页.html`。
4. 校验 DOI、PubMed URL、译文和网页内嵌数据。
5. 提交更新并部署到 GitHub Pages。

也可以在仓库的 Actions 页面手动运行 `Update literature and deploy Pages`。

## 本地更新

```powershell
python scripts/update_literature.py --retmax 220
python scripts/translate_literature.py
python scripts/generate_static_site.py
python scripts/validate_literature.py
```

中文题名和摘要由自动翻译生成，科研引用和专业术语应以 PubMed 英文原文为准。
