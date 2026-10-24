"""编译技术方案与佐证材料，并复制到 materials/。需要 TeX Live（XeLaTeX、ctex、latexmk）。"""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
compiler = shutil.which('latexmk') or ('/Library/TeX/texbin/latexmk' if Path('/Library/TeX/texbin/latexmk').exists() else None)
if not compiler:
    raise SystemExit('请先安装 TeX Live / MacTeX（含 XeLaTeX、ctex 与 latexmk）。')
for tex, name in [('main.tex', '墒策_技术方案.pdf'), ('evidence.tex', '墒策_佐证材料.pdf')]:
    subprocess.run([compiler, '-xelatex', '-interaction=nonstopmode', '-file-line-error', '-halt-on-error', tex],
                   cwd=ROOT / 'paper', check=True)
    shutil.copy2(ROOT / 'paper' / tex.replace('.tex', '.pdf'), ROOT / 'materials' / name)
    print('已生成', ROOT / 'materials' / name)
