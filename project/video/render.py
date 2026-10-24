"""合成演示视频：录屏 + 解说音轨 + 字幕。
用法：python video/render.py  （需先运行 synth 生成 narration.wav/timeline.json，并运行 record.cjs）
输出：materials/墒策_演示视频.mp4、video/墒策_演示视频_字幕.srt，以及无配音版本（便于团队成员自行录音）。"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
tl = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))
rec = json.loads((HERE / "build" / "recording.json").read_text())
dur = tl[-1]["end"]


def ts_ass(t):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ts_srt(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def clean(s):
    return s.rstrip("。")


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1600", "PlayResY: 1000", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,Noto Sans CJK SC,38,&H00FFFFFF,&H00FFFFFF,&H50203A2F,&H50203A2F,0,0,0,0,100,100,1,0,3,14,0,2,120,120,46,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
srt = []
n = 0
for sc in tl:
    for ln in sc["lines"]:
        n += 1
        a, b = ln["start"], ln["end"] + 0.25
        ass.append(f"Dialogue: 0,{ts_ass(a)},{ts_ass(b)},Sub,,0,0,0,,{clean(ln['text'])}")
        srt += [str(n), f"{ts_srt(a)} --> {ts_srt(b)}", clean(ln["text"]), ""]
(HERE / "build" / "subs.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")
(HERE / "墒策_演示视频_字幕.srt").write_text("\n".join(srt), encoding="utf-8")

src = rec["path"]
off = rec["offset_s"]
vf = "fps=25,format=yuv420p,subtitles=build/subs.ass"
common = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", "-t", f"{dur:.3f}"]
out = ROOT / "materials" / "墒策_演示视频.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{off:.3f}", "-i", src, "-i", "narration.wav", "-map", "0:v", "-map", "1:a",
                "-vf", vf, *common, "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(out)], check=True, cwd=HERE)
silent = HERE / "墒策_演示视频_无配音版.mp4"
subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{off:.3f}", "-i", src, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                "-map", "0:v", "-map", "1:a", "-vf", vf, *common, "-c:a", "aac", "-b:a", "96k", "-shortest", str(silent)], check=True, cwd=HERE)
print("written", out, silent)
