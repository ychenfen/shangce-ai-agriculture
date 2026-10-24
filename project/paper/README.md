# 技术方案与佐证材料源文件

- `main.tex`：技术方案主文件，章节位于 `chapters/`，表格位于 `tables/`，图表位于 `figures/`
- `evidence.tex`：佐证材料
- 编译：`latexmk -xelatex main.tex`、`latexmk -xelatex evidence.tex`（需 TeX Live + ctex）
- 图表与统计表由 `scripts/report_analysis.py` 从 `results/` 中的 CSV 生成；系统截图位于 `results/screenshots/`
