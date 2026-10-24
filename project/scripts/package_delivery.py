"""打包完整工程，用于上传百度网盘（作品其他材料链接）。
命名遵循大赛要求：参赛团队编号-赛题名称-作品名称-XX（材料名称）。
用法：python scripts/package_delivery.py  → dist/ 下生成 ZIP 与 SHA-256 清单。"""
from pathlib import Path
import hashlib
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "AIC-2026-54247845-AI+农业-墒策"
DIST = ROOT / "dist"
SKIP_DIRS = {"__pycache__", ".venv", "build", "dist", ".pytest_cache", ".git"}
SKIP_SUFFIX = {".pyc", ".log", ".aux", ".toc", ".out", ".fls", ".xdv", ".fdb_latexmk", ".gz", ".synctex"}

# 提交材料单独按规范命名，同时放入根目录
NAMED = {
    "materials/墒策_技术方案.pdf": f"{PREFIX}-技术方案.pdf",
    "materials/墒策_答辩演示.pdf": f"{PREFIX}-答辩PPT.pdf",
    "materials/墒策_答辩演示.pptx": f"{PREFIX}-答辩PPT源文件.pptx",
    "materials/墒策_演示视频.mp4": f"{PREFIX}-演示视频.mp4",
    "materials/墒策_佐证材料.pdf": f"{PREFIX}-佐证材料.pdf",
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def wanted(p):
    rel = p.relative_to(ROOT)
    if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts):
        return False
    if p.suffix in SKIP_SUFFIX or rel.as_posix() == "materials/报名字段.md":
        return False
    if rel.parts[0] in ("video", "materials") and p.suffix in (".wav", ".mp4"):
        return False  # 视频已在根目录单独提供
    return p.is_file()


def main():
    DIST.mkdir(exist_ok=True)
    files = sorted(p for p in ROOT.rglob("*") if wanted(p))
    code_zip = DIST / f"{PREFIX}-完整代码包.zip"
    with zipfile.ZipFile(code_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, f"{PREFIX}-完整代码包/{p.relative_to(ROOT).as_posix()}")
        sums = "".join(f"{sha(p)}  {p.relative_to(ROOT).as_posix()}\n" for p in files)
        z.writestr(f"{PREFIX}-完整代码包/SHA256SUMS.txt", sums)
    with zipfile.ZipFile(code_zip) as z:
        assert z.testzip() is None
    folder = DIST / PREFIX
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir()
    for src, name in NAMED.items():
        shutil.copy2(ROOT / src, folder / name)
    shutil.move(str(code_zip), folder / code_zip.name)
    lines = [f"{sha(p)}  {p.name}\n" for p in sorted(folder.iterdir())]
    (folder / "SHA256SUMS.txt").write_text("".join(lines), encoding="utf-8")
    print(folder, len(files), "files in code package")


if __name__ == "__main__":
    main()
