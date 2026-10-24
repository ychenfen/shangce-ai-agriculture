# 墒策：可信需水预测与灌溉决策

第八届全球校园人工智能算法精英大赛 · 算法主题赛 · AI＋农业
团队名称：得分队　团队编号：AIC-2026-54247845

“墒”取自土壤墒情（根区土壤水分状况），“策”指灌溉决策。墒策把次日需水预测、经独立年份校准的预测区间和 FAO-56 根区水量平衡连成一条决策链，回答“明天要不要灌、灌多少、能不能补够”。

## 核心结果

- 数据：石家庄、郑州、济南三地 2018—2025 年 ERA5 逐日气象，共 8766 条（Open-Meteo，CC BY 4.0）
- 划分：2018—2022 训练 5457 条，2023 校准 1095 条，2024—2025 测试 2193 条
- 预测：MAE 0.7757 mm/日，较昨日值基线降低 7.68%；RMSE 1.0688；R² 0.7103
- 区间：名义 90% 预测区间测试覆盖率 91.06%，平均宽度 3.61 mm/日
- 仿真：180 组生长季，基准情景下区间上界策略缺水风险日为 0，较定额日历灌溉少用水 31.4%

## 快速开始

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app/server.py --port 8765
```

浏览器打开 <http://127.0.0.1:8765>。macOS 可双击 `启动墒策.command`，Windows 可双击 `启动墒策.bat`。原始数据与已训练模型随工程提供，运行无需联网。

## 复现实验

```sh
.venv/bin/python -m src.pipeline            # 训练、评估、迁移检验与 180 组仿真
.venv/bin/python -m pytest -q               # 核心单元测试（9 项）
.venv/bin/python scripts/report_analysis.py # 诊断统计与报告图表
.venv/bin/python scripts/verify_delivery.py # 从 CSV 重算指标并核验交付文件
```

重新下载原始数据：`scripts/fetch_inputs.py`（已有文件会复用，请求与哈希记录在 `inputs/provenance.json`）。

## 目录

| 位置 | 内容 |
| --- | --- |
| `src/pipeline.py` | 数据校验、特征构造、模型训练、共形校准、对照与迁移检验、策略仿真 |
| `src/agro.py` | FAO-56 水量平衡、灌溉建议与参数校验 |
| `app/` | 本地推理服务与交互界面 |
| `models/shangce.joblib` | 已训练模型、特征列表、校准分位数 |
| `inputs/weather/` | 三地原始接口响应 |
| `results/` | 逐日预测、180 组仿真明细、汇总与测试记录、系统截图 |
| `paper/` | 技术方案与佐证材料的 LaTeX 源文件（XeLaTeX + ctex 编译） |
| `materials/` | 技术方案、答辩 PPT/PDF、演示视频、佐证材料 |
| `video/` | 演示视频的解说词、时间轴、录屏与合成脚本 |
| `scripts/` | 数据获取、图表、答辩 PPT 生成、浏览器测试与交付核验 |

## 文档编译

- 技术方案：在 `paper/` 下运行 `latexmk -xelatex main.tex`
- 佐证材料：在 `paper/` 下运行 `latexmk -xelatex evidence.tex`
- 答辩 PPT：`python scripts/build_slides.py`（需 python-pptx），PDF 由 LibreOffice 导出

数据来源与第三方许可见 `THIRD_PARTY.md`。
