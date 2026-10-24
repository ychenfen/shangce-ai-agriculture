# 数据来源与第三方许可

- **气象数据**：Open-Meteo Historical Weather API（`models=era5`，Asia/Shanghai 逐日聚合），数据基于 ECMWF ERA5 再分析。数据许可 CC BY 4.0：<https://open-meteo.com/en/licence>。原始响应未改写，请求 URL 与 SHA-256 见 `inputs/provenance.json`。本项目的特征、预测与仿真结果为对原始数据的再处理，不代表数据提供方的结论。
- **方法**：FAO-56（Allen, Pereira, Raes, Smith, 1998）作物蒸散与灌溉需水计算方法；分割式共形预测（Vovk 等, 2005；Lei 等, 2018）。公式按文献自行编程实现。
- **软件依赖**：NumPy、pandas、scikit-learn、joblib、Matplotlib、pytest、python-pptx、Playwright，均遵循各自开源许可；工程列出依赖版本，不打包安装环境。
- **界面**：HTML/CSS/JavaScript 为本项目编写，未使用外部图片、地图瓦片或图标库。
- **文档与视频**：技术方案与佐证材料由 XeLaTeX/ctex 排版（Fandol 字体）；演示视频为系统实际运行录屏，解说为合成语音（sherpa-onnx Kokoro 中文模型）。
