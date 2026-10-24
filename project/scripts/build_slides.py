"""生成答辩PPT：python scripts/build_slides.py  → materials/墒策_答辩演示.pptx
依赖 python-pptx；数据取自 results/summary.json 与 results/report_monthly.csv。"""
import csv, json
from pathlib import Path
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "materials" / "墒策_答辩演示.pptx"
S = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
MONTHLY = list(csv.DictReader(open(ROOT / "results" / "report_monthly.csv", encoding="utf-8")))

FONT = "Microsoft YaHei"
FOREST = RGBColor(0x24, 0x4F, 0x3B)
INK = RGBColor(0x22, 0x2B, 0x26)
MUTED = RGBColor(0x6B, 0x75, 0x6C)
PAPER = RGBColor(0xF6, 0xF3, 0xEC)
SAGE = RGBColor(0xDD, 0xE7, 0xD3)
CLAY = RGBColor(0xA8, 0x6B, 0x43)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LINE = RGBColor(0xD5, 0xDB, 0xCE)

prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]
CM = 360000


def cm(x):
    return Emu(int(x * CM))


def bg(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def text(slide, x, y, w, h, s, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, spacing=1.15, font=FONT):
    tb = slide.shapes.add_textbox(cm(x), cm(y), cm(w), cm(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = s if isinstance(s, list) else [s]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        runs = line if isinstance(line, list) else [(line, {})]
        for r in runs:
            if isinstance(r, str):
                r = (r, {})
            run = p.add_run()
            run.text = r[0]
            fnt = run.font
            fnt.name = font
            fnt.size = Pt(r[1].get("size", size))
            fnt.bold = r[1].get("bold", bold)
            fnt.color.rgb = r[1].get("color", color)
    return tb


def rect(slide, x, y, w, h, fill=SAGE, line=None, shape=MSO_SHAPE.RECTANGLE):
    sh = slide.shapes.add_shape(shape, cm(x), cm(y), cm(w), cm(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh


def header(slide, n, title, sub=None):
    bg(slide, PAPER)
    rect(slide, 0, 0, 0.35, 19.05, FOREST)
    text(slide, 1.6, 1.0, 26, 1.4, title, size=26, color=FOREST, bold=True)
    if sub:
        text(slide, 1.6, 2.45, 28, 0.8, sub, size=13, color=MUTED)
    text(slide, 30.4, 17.9, 2.4, 0.6, f"{n:02d}", size=10, color=MUTED, align=PP_ALIGN.RIGHT)
    text(slide, 1.6, 17.9, 18, 0.6, "墒策 · 可信需水预测与灌溉决策    得分队", size=10, color=MUTED)


def card(slide, x, y, w, h, title, body, num=None, fill=WHITE):
    rect(slide, x, y, w, h, fill, LINE)
    if num:
        text(slide, x + 0.6, y + 0.5, 3, 1.0, num, size=22, color=CLAY, bold=True)
        ty = y + 1.7
    else:
        ty = y + 0.6
    text(slide, x + 0.6, ty, w - 1.2, 0.9, title, size=19, color=FOREST, bold=True)
    text(slide, x + 0.6, ty + 1.4, w - 1.2, h - (ty - y) - 1.6, body, size=15, color=INK, spacing=1.45)


def table(slide, x, y, w, rows, colw=None, size=13, rowh=1.0, hl=None):
    nr, nc = len(rows), len(rows[0])
    gt = slide.shapes.add_table(nr, nc, cm(x), cm(y), cm(w), cm(rowh * nr)).table
    if colw:
        for i, c in enumerate(colw):
            gt.columns[i].width = cm(c)
    for r in range(nr):
        gt.rows[r].height = cm(rowh)
        for c in range(nc):
            cell = gt.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = FOREST if r == 0 else (SAGE if hl is not None and r == hl else WHITE)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = cm(0.3)
            tf = cell.text_frame
            tf.text = ""
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = str(rows[r][c])
            run.font.name = FONT
            run.font.size = Pt(size)
            run.font.bold = r == 0 or (hl is not None and r == hl)
            run.font.color.rgb = WHITE if r == 0 else INK
    return gt


def big(slide, x, y, value, label, color=FOREST, size=40, w=8):
    hv = size * 0.055 + 0.3
    text(slide, x, y, w, hv, value, size=size, color=color, bold=True)
    text(slide, x, y + hv + 0.2, w, 1.4, label, size=12, color=MUTED, spacing=1.25)


m = S["metrics"]
mae, persist = m["ai"]["mae"], m["persistence"]["mae"]
cov = S["interval"]["all"]["coverage"] * 100
width = S["interval"]["all"]["width"]
central = S["simulation"]["central"]
tr = S["transfer"]

# 1 封面 --------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
bg(s, FOREST)
text(s, 2.4, 2.0, 20, 0.8, "2026 第八届全球校园人工智能算法精英大赛 · 算法主题赛 · AI＋农业", size=13, color=SAGE)
text(s, 2.4, 4.2, 20, 3.4, "墒策", size=80, color=WHITE, bold=True)
text(s, 2.4, 7.9, 22, 1.4, "可信需水预测与灌溉决策", size=30, color=WHITE)
rect(s, 2.4, 10.0, 2.2, 0.08, CLAY)
text(s, 2.4, 10.6, 24, 1.8, ["“墒”取自土壤墒情——根区土壤的水分状况；“策”指灌溉决策。",
                             "墒策：依墒情定灌溉之策，让需水预测带着误差范围进入灌溉决策。"], size=14, color=SAGE, spacing=1.4)
text(s, 2.4, 15.2, 24, 1.6, [[("团队名称  ", {"color": SAGE}), ("得分队", {"bold": True, "color": WHITE})],
                             [("团队编号  ", {"color": SAGE}), ("AIC-2026-54247845", {"bold": True, "color": WHITE})]],
     size=14, spacing=1.5)

# 2 背景 --------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 2, "背景：华北灌溉“灌不灌、灌多少”靠经验", "粮食主产区与地下水超采区高度重叠，灌溉决策直接关系稳产与节水")
card(s, 1.6, 4.4, 9.6, 8.6, "需水看不到明天",
     "作物耗水随辐射、温度、湿度、风速逐日变化，5—7 月日参考蒸散可达 6～9 mm。“昨天耗多少、今天补多少”在天气转折时明显滞后。", "01")
card(s, 11.9, 4.4, 9.6, 8.6, "预测没有误差范围",
     "单一预测值无法回答“如果偏低会怎样”。经验做法往往多灌对冲风险，造成浪费与深层渗漏；精确按均值灌又可能缺水。", "02")
card(s, 22.2, 4.4, 9.6, 8.6, "建议脱离土壤与设备",
     "同样的需水，对墒情充足的地块无需灌溉，对接近阈值的地块必须补水；机井出水、轮灌时段又限制了当天能补多少。", "03")
rect(s, 1.6, 14.0, 30.2, 2.2, SAGE)
text(s, 2.4, 14.0, 29, 2.2, [[("核心痛点：", {"bold": True, "color": CLAY}), "预测、误差、土壤与设备之间缺少一条贯通、可检查的决策链。"]], size=17, anchor=MSO_ANCHOR.MIDDLE)

# 3 作品定位 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 3, "墒策是什么", "把“次日需水预测—误差区间—根区水量—供水约束”连成一条可检查的决策链")
text(s, 1.6, 4.4, 13.5, 8, [
    [("一句话：", {"bold": True, "color": FOREST})],
    "输入地区、日期和地块参数，系统给出次日作物需水、90% 预测区间，以及“灌不灌、灌多少、能不能补够”的建议，并保留完整依据。",
    "",
    [("目标用户", {"bold": True, "color": FOREST})],
    "基层农技人员：比较不同灌溉情景，为农户提供建议",
    "农业水利 / 智慧农业课程：直观理解 FAO-56 水量平衡",
], size=15, spacing=1.45)
for i, (k, v) in enumerate([("次日需水预测", "梯度提升树，49 维时间安全特征"),
                            ("误差可量化", "2023 年独立校准的 90% 预测区间"),
                            ("预测进决策", "FAO-56 根区水量平衡＋供水上限"),
                            ("过程可追溯", "服务端重算，决策记录一键导出")]):
    y = 4.3 + i * 3.2
    rect(s, 17.0, y, 14.8, 2.7, WHITE, LINE)
    rect(s, 17.0, y, 0.25, 2.7, FOREST)
    text(s, 17.9, y + 0.45, 13, 0.9, k, size=17, color=FOREST, bold=True)
    text(s, 17.9, y + 1.45, 13, 0.9, v, size=13, color=INK)

# 4 技术路线 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 4, "技术路线：机理与数据耦合", "数据驱动模型负责短期需水预测，FAO-56 机理公式处理土壤、作物与设备约束")
boxes = [("数据层", "三地 ERA5 逐日气象\n2018—2025 · 8,766 条\n质量检查与哈希归档"),
         ("预测层", "49 维历史特征\n梯度提升树回归\n次日参考蒸散 ET₀"),
         ("不确定性", "2023 年独立校准\n分割式共形预测\n90% 预测区间"),
         ("决策层", "ET₀ × 作物系数\n根区亏缺触发与回填\n日供水上限约束")]
bx = []
for i, (t, b) in enumerate(boxes):
    x = 1.6 + i * 7.75
    rect(s, x, 4.6, 6.6, 1.3, FOREST)
    text(s, x, 4.6, 6.6, 1.3, t, size=17, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, x, 5.9, 6.6, 4.4, WHITE, LINE)
    text(s, x + 0.4, 6.3, 5.8, 3.8, b.split("\n"), size=13, align=PP_ALIGN.CENTER, spacing=1.5)
    bx.append(x)
    if i < 3:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, cm(x + 6.75), cm(7.4), cm(0.85), cm(0.8))
        a.fill.solid(); a.fill.fore_color.rgb = CLAY; a.line.fill.background()
for i, (t, b) in enumerate([("交互系统", "历史回放 · 参数调节 · 供水检查 · 记录导出"),
                            ("策略仿真", "5 种策略 × 36 个情景 = 180 组生长季")]):
    x = 1.6 + i * 15.5
    rect(s, x, 11.6, 14.7, 3.0, SAGE)
    text(s, x + 0.6, 11.95, 13.5, 0.9, t, size=16, color=FOREST, bold=True)
    text(s, x + 0.6, 13.15, 13.5, 1.0, b, size=13)
text(s, 1.6, 15.4, 30, 1.6, "工具：Python 3.12 · pandas · scikit-learn 1.7 · 原生 HTML/JS 本地服务 · pytest / Playwright 测试；全部离线运行，普通笔记本即可部署",
     size=12, color=MUTED)

# 5 数据与时间隔离 --------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 5, "数据与时间隔离", "石家庄、郑州、济南三地 ERA5 再分析逐日气象（Open-Meteo，CC BY 4.0）")
big(s, 1.6, 4.4, "8,766", "条逐日记录 · 三地各 2,922 天\n无缺失，原始响应与 SHA-256 完整保留", size=54, w=12)
segs = [("2018—2022", "训练", "5,457 条", 5, FOREST), ("2023", "校准", "1,095 条", 1, CLAY), ("2024—2025", "测试", "2,193 条", 2, RGBColor(0x5E, 0x7F, 0x8C))]
x0, tot = 1.6, 30.2
x = x0
for yr, name, n, k, col in segs:
    w = tot * k / 8
    rect(s, x, 10.6, w - 0.15, 1.6, col)
    text(s, x, 10.6, w - 0.15, 1.6, f"{name}  {n}", size=15, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x, 12.4, w, 0.8, yr, size=13, color=MUTED, align=PP_ALIGN.CENTER)
    x += w
text(s, 15.5, 4.6, 16.3, 5, [
    [("时间安全的特征", {"bold": True, "color": FOREST})],
    "只用目标日之前的数据：滞后 1/2/3/7 天＋“先滞后、再取 7 日均值”",
    "单元测试：大幅扰动目标日及之后数据，49 维特征保持不变",
    [("严格按年份切分", {"bold": True, "color": FOREST})],
    "模型只在训练年拟合，校准年只估计误差分位数，测试年不参与任何调参",
], size=13, spacing=1.45)
text(s, 1.6, 14.2, 30, 1.6, "9 个变量：平均/最高/最低气温、相对湿度、10 m 风速、降水、短波辐射、地表气压、历史参考蒸散 ET₀",
     size=13, color=INK)

# 6 核心技术 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 6, "核心技术：预测 → 区间 → 决策", "每一步都有明确公式，可手工复核")
cols = [("① 梯度提升树", ["9 变量 × 5 种滞后/均值 = 45", "＋经纬度＋日期周期编码 = 49 维", "180 轮 · 学习率 0.055 · 15 叶 · L2=8", "超参数在接触测试集前固定"]),
        ("② 共形预测区间", ["2023 年 1,095 条校准残差", "取第 987 小的绝对残差", f"q = {S['q90']:.3f} mm/日", "区间 = 预测 ± q（下界截至 0）"]),
        ("③ FAO-56 灌溉决策", ["预计亏缺 D* = D + Kc × ET₀", "D* > 0.5·TAW 时触发", "毛灌溉 = (D* − 0.25·TAW) / η", "并受日供水上限 C 约束"])]
for i, (t, lines) in enumerate(cols):
    x = 1.6 + i * 10.3
    rect(s, x, 4.2, 9.6, 10.6, WHITE, LINE)
    rect(s, x, 4.2, 9.6, 1.4, FOREST)
    text(s, x, 4.2, 9.6, 1.4, t, size=17, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.6, 6.3, 8.4, 8, lines, size=14, spacing=1.8)
text(s, 1.6, 15.5, 30, 1.2, [[("关键设计：", {"bold": True, "color": CLAY}), "可选用“点预测”或“区间上界”进入决策——上界策略用少量额外用水换取更低缺水风险，由使用者按地块情况选择。"]],
     size=13)

# 7 系统演示 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 7, "系统演示：需水与灌溉工作台", "本地服务实时推理；参数变化后，图形、建议与导出记录同步更新")
s.shapes.add_picture(str(ROOT / "results/screenshots/dashboard.png"), cm(1.6), cm(3.9), height=cm(13.2))
text(s, 23.3, 4.2, 8.6, 13, [
    [("首屏四项", {"bold": True, "color": FOREST})], "预测 ET₀ · 90% 区间 · 昨日值基线 · 事后参考值", "",
    [("曲线图", {"bold": True, "color": FOREST})], "阴影为预测区间，可悬停逐日查看，30/90 日切换", "",
    [("参数面板", {"bold": True, "color": FOREST})], "亏缺、TAW、效率、供水上限、Kc 与策略，实时给出补水量", "",
    [("供水受限", {"bold": True, "color": FOREST})], "超过上限时按上限给出补水量并提示后续补灌", "",
    [("记录导出", {"bold": True, "color": FOREST})], "JSON 保存输入、模型版本与结果"], size=12, spacing=1.3)

# 8 预测精度 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 8, f"预测精度：MAE 较昨日值降低 {S['mae_improvement_pct']:.2f}%", "2024—2025 年三地 2,193 条时间留出样本；所有方法在测试期均未调参")
cd = CategoryChartData()
order = [("climatology", "地区月均值"), ("persistence", "昨日值"), ("calendar_only", "日期与位置"), ("no_et_history", "去除历史ET₀"), ("ai", "墒策")]
order = [(k, n) for k, n in order if k in m]
cd.categories = [n for _, n in order]
cd.add_series("MAE", [round(m[k]["mae"], 3) for k, _ in order])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, cm(1.6), cm(3.9), cm(18), cm(12.6), cd)
ch = gf.chart
ch.has_title = False
ch.has_legend = False
ch.font.name = FONT; ch.font.size = Pt(12)
plot = ch.plots[0]; plot.gap_width = 70; plot.has_data_labels = True
dl = plot.data_labels; dl.number_format = "0.000"; dl.number_format_is_linked = False; dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size = Pt(12)
ser = plot.series[0]
for i, (k, _) in enumerate(order):
    pt = ser.points[i]
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = FOREST if k == "ai" else RGBColor(0xB8, 0xC4, 0xB2)
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 1.2; va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(11)
va.has_title = True; va.axis_title.text_frame.text = "MAE / mm·日⁻¹"
va.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
ch.category_axis.tick_labels.font.size = Pt(12)
big(s, 21.0, 4.3, f"{mae:.4f}", "MAE（mm/日）\n昨日值基线 0.8403", w=10)
big(s, 21.0, 8.3, f"{m['ai']['r2']:.3f}", f"决定系数 R²\nRMSE {m['ai']['rmse']:.4f} mm/日", w=10)
text(s, 21.0, 12.4, 10.8, 4, ["块自助重采样：MAE 差值 95% 区间 [0.033, 0.097]，不含 0，改进稳定",
                              "去除历史 ET₀ 后 MAE 仅升至 0.7800：模型主要依赖原始气象变量，便于改接地面气象站"], size=12, spacing=1.35)

# 9 区间与季节诊断 ---------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 9, f"预测区间：全年覆盖率 {cov:.2f}%，夏季需加强", "分月诊断定位了下一步优化目标")
cd = CategoryChartData()
cd.categories = [f"{int(r['month'])}月" for r in MONTHLY]
cd.add_series("经验覆盖率 %", [round(float(r["coverage"]) * 100, 1) for r in MONTHLY])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, cm(1.6), cm(3.9), cm(19.5), cm(12.8), cd)
ch = gf.chart; ch.has_title = False; ch.has_legend = False; ch.font.name = FONT; ch.font.size = Pt(11)
plot = ch.plots[0]; plot.gap_width = 45; plot.has_data_labels = True
plot.data_labels.number_format = "0"; plot.data_labels.number_format_is_linked = False
plot.data_labels.font.size = Pt(10); plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
for i, r in enumerate(MONTHLY):
    pt = plot.series[0].points[i]; pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = CLAY if float(r["coverage"]) < 0.9 else FOREST
va = ch.value_axis; va.minimum_scale = 60; va.maximum_scale = 105; va.major_unit = 10
va.has_title = True; va.axis_title.text_frame.text = "经验覆盖率 / %"
va.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
va.major_gridlines.format.line.color.rgb = LINE; va.tick_labels.font.size = Pt(10)
big(s, 22.4, 4.3, f"{cov:.2f}%", f"测试集 90% 区间实际覆盖率\n平均宽度 {width:.2f} mm/日；上下两侧失覆盖 102 / 94 条", w=10)
text(s, 22.4, 9.0, 9.4, 7.5, [
    [("发现", {"bold": True, "color": CLAY})],
    "区间半宽全年固定，冬季偏宽（覆盖 100%），6、7 月覆盖降至 78.3% 和 79.0%",
    "夏季点预测仍优于昨日值（6 月 MAE 1.268 对 1.456）",
    [("改进", {"bold": True, "color": FOREST})],
    "分季节校准 / 共形分位数回归，让区间随天气自适应"], size=12, spacing=1.35)

# 10 跨地区迁移 ----------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 10, "跨地区迁移：没见过的地区也优于基线", "每次完全排除目标地区的训练与校准数据，用另外两地建模")
names = {"shijiazhuang": "石家庄", "zhengzhou": "郑州", "jinan": "济南"}
rows = [["留出地区", "模型 MAE", "昨日值 MAE", "降低", "区间覆盖率"]]
for k in ["shijiazhuang", "zhengzhou", "jinan"]:
    v = tr[k]
    rows.append([names[k], f"{v['mae']:.3f}", f"{v['persistence_mae']:.3f}", f"{(1 - v['mae'] / v['persistence_mae']) * 100:.1f}%", f"{v['coverage'] * 100:.2f}%"])
table(s, 1.6, 4.6, 19.5, rows, colw=[4.3, 3.8, 3.8, 3.4, 4.2], size=15, rowh=1.5)
text(s, 22.4, 4.6, 9.4, 11, [
    [("结论", {"bold": True, "color": FOREST})],
    "三地点预测均优于当地昨日值基线，降低 5.3%～8.4%",
    "石家庄、济南覆盖率保持 90% 以上",
    "",
    [("推广方式", {"bold": True, "color": FOREST})],
    "部署到新地区时，可用当地一年数据重新校准区间（有待实地验证），模型结构无需改动"], size=14, spacing=1.4)
text(s, 1.6, 12.0, 19.5, 3, "分地区分年份评价中，三地两年共 6 个分组的模型 MAE 全部低于昨日值；郑州 2024 年降低 14.2%。",
     size=13, color=MUTED, spacing=1.4)

# 11 策略仿真 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 11, "灌溉策略仿真：提前一天看需水，仿真缺水风险日下降", "基准情景：TAW 120 mm、灌溉效率 0.85、日供水上限 40 mm；三地两年六个生长季平均")
lab = [("calendar", "定额日历（每 7 天 25 mm）"), ("sensor", "墒情阈值（只看当前亏缺）"), ("persistence", "昨日值预测"), ("ai", "AI 点预测"), ("upper", "AI 区间上界")]
rows = [["策略", "毛灌溉量 / mm", "缺水风险日", "排水 / mm"]]
for k, n in lab:
    v = central[k]
    rows.append([n, f"{v['irrigation_mm']:.2f}", f"{v['stress_days']:.2f}", f"{v['drainage_mm']:.2f}"])
table(s, 1.6, 4.2, 20.0, rows, colw=[8.2, 4.2, 3.8, 3.8], size=14, rowh=1.35, hl=5)
text(s, 22.6, 4.2, 9.2, 12, [
    [("对比定额日历", {"bold": True, "color": FOREST})], "用水减少 31.4%，风险日 8.83 → 0", "",
    [("对比墒情阈值", {"bold": True, "color": FOREST})], "多用约 25 mm，风险日 9.33 → 0", "",
    [("环境内配对（36 个情景）", {"bold": True, "color": FOREST})], "上界策略相对 AI 点预测：27 个情景风险更低、9 个持平、0 个更高；平均多用 5.65 mm"],
    size=13, spacing=1.35)
text(s, 1.6, 13.0, 20, 3.2, ["180 组生长季仿真：3 地 × 2 年 × 3 档 TAW × 2 档效率 × 5 种策略，共 27,540 条逐日水量记录。",
                             "在全部 6 种“容量—效率”组合中，区间上界策略风险日始终最低（0～0.17 日）。"], size=12, color=MUTED, spacing=1.4)

# 12 创新点 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 12, "创新点")
items = [("把预测误差放进灌溉决策", "独立年份校准的预测区间直接参与触发规则，用户可在“少用水”和“少缺水”之间知情选择"),
         ("机理与数据耦合", "梯度提升树做短期需水预测，FAO-56 水量平衡处理土壤、作物与设备约束"),
         ("供水能力显式建模", "超过日供水上限时按上限给出可执行补水量，并提示补水后预计亏缺"),
         ("严格时间隔离、全链条可复现", "扰动测试保证无信息泄漏；原始数据、模型、逐日结果与脚本全部交付"),
         ("诊断驱动的改进", "分月、分地区、极端误差诊断，明确夏季区间与天气突变两大优化方向")]
for i, (t, b) in enumerate(items):
    y = 3.9 + i * 2.75
    rect(s, 1.6, y, 30.2, 2.35, WHITE, LINE)
    text(s, 2.2, y, 1.6, 2.35, f"{i + 1}", size=26, color=CLAY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 4.0, y + 0.35, 9.8, 1.7, t, size=16, color=FOREST, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 14.0, y + 0.35, 17.3, 1.7, b, size=13, anchor=MSO_ANCHOR.MIDDLE, spacing=1.3)

# 13 应用前景 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 13, "应用前景与效益", "部署门槛低、计算过程透明，适合在基层推广")
card(s, 1.6, 4.2, 9.6, 8.0, "农技服务", "作为农技站、合作社的灌溉参谋：选择地块参数即可得到补水建议与依据，向农户解释“为什么灌、灌多少”。")
card(s, 11.9, 4.2, 9.6, 8.0, "灌区信息化", "为墒情监测数据提供“下一步怎么做”的决策出口，可嵌入灌区平台，支持轮灌排班与有限水源分配。")
card(s, 22.2, 4.2, 9.6, 8.0, "教学科研", "农业水利、智慧农业课程的实践工具；开放的数据与逐日结果便于复现与扩展研究。")
for i, (v, l) in enumerate([("416 KiB", "模型文件大小"), ("≈11.5 ms", "单次推理中位耗时"), ("0", "运行时外部依赖服务"), ("11%～37%", "仿真中上界策略较定额日历节水")]):
    big(s, 1.6 + i * 7.75, 13.5, v, l, size=26, w=7.4)

# 14 下一步 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
header(s, 14, "下一步计划", "从历史回测走向田间验证")
steps = [("模型升级", "自适应区间（分季节校准、共形分位数回归）；接入未来 1～3 天天气预报，扣减预报降雨"),
         ("接入墒情", "对接土壤水分传感器，实测亏缺替代输入值，在线修正 TAW 与作物系数"),
         ("影子运行", "试点地块每日给出建议、农艺人员照常决策，积累对比数据"),
         ("对照试验", "可比地块开展系统建议与常规管理对照，量化节水率、产量与能耗")]
for i, (t, b) in enumerate(steps):
    x = 1.6 + i * 7.75
    rect(s, x, 4.6, 6.9, 1.4, FOREST if i == 0 else SAGE)
    text(s, x, 4.6, 6.9, 1.4, f"阶段 {i + 1}  {t}", size=16, color=WHITE if i == 0 else FOREST, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, x, 6.0, 6.9, 7.0, WHITE, LINE)
    text(s, x + 0.5, 6.5, 5.9, 6, b, size=13, spacing=1.5)
text(s, 1.6, 14.0, 30, 2, "长期目标：多地块联合调度——在共享水源与管网容量约束下，按缺水风险排序分配有限供水能力。", size=14, color=INK)

# 15 致谢 ------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
bg(s, FOREST)
text(s, 0, 6.0, 33.87, 3, "谢谢！", size=60, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
text(s, 0, 9.6, 33.87, 1.2, "墒策 · 可信需水预测与灌溉决策", size=20, color=SAGE, align=PP_ALIGN.CENTER)
text(s, 0, 12.4, 33.87, 1.2, "得分队    AIC-2026-54247845", size=16, color=SAGE, align=PP_ALIGN.CENTER)

cp = prs.core_properties
cp.title = "墒策：可信需水预测与灌溉决策"
cp.author = "得分队"
cp.last_modified_by = "得分队"
cp.comments = ""
cp.subject = "AI＋农业 答辩"
import datetime as _dt
cp.created = cp.modified = _dt.datetime(2026, 10, 24, 9, 0)
cp.revision = 1
cp.last_printed = _dt.datetime(2026, 10, 24, 9, 0)
prs.save(OUT)
# 清理模板遗留的应用程序属性
import zipfile, shutil, re as _re
tmp = OUT.with_suffix(".tmp.pptx")
with zipfile.ZipFile(OUT) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "docProps/app.xml":
            s = data.decode("utf-8")
            s = _re.sub(r"<Application>.*?</Application>", "<Application>Microsoft Office PowerPoint</Application>", s)
            s = _re.sub(r"<PresentationFormat>.*?</PresentationFormat>", "<PresentationFormat>宽屏</PresentationFormat>", s)
            s = _re.sub(r"<Company>.*?</Company>", "<Company></Company>", s)
            data = s.encode("utf-8")
        zout.writestr(item, data)
shutil.move(tmp, OUT)
print("saved", OUT, len(prs.slides), "slides")
