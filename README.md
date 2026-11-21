# 声场衰减提取台

礼堂声学验收工程师可导入预分带的脉冲响应，复核量纲、能量曲线、T20 与 T30 回归和噪声判定。应用保存原始收件，导出可重算的复测证据。

```bash
docker compose up --build
docker compose exec -T app pytest -q
```

打开 [工作台](http://localhost:18430/) 或 [接口文档](http://localhost:18430/docs)。首页先展示礼堂样例预览。「运行提取」归档当前来源，「中心频率」联动曲线与拟合区间，「定位采样点」显示秒数、相对 dB 与来源行。「复测归档」可打开历史结果和重跑，顶部「导出证据」保存一份 JSON。可切换 GB18030 参考样例或在「脉冲响应收件」上传响应 CSV。

### 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --port 18430
```

SQLite 使用 Compose 命名卷 `measurements`。应用启动按内容摘要幂等入库内置响应。如需清空所有收件和归档，确认后执行 `docker compose down -v`。

## 业务入口

| 模块 | API | 核查内容 |
|---|---|---|
| 脉冲响应收件 | `POST /api/intake`、`GET /api/intake/sample/hall` | 样本连续性与隔离 |
| 量纲校准 | `GET /api/calibration/{source_id}` | 增益、灵敏度、峰值与有效源行 |
| 能量衰减 | `GET /api/decay/{source_id}` | 反向能量积分与原点 |
| 拟合时段 | `GET /api/fit/{source_id}` | 回归区间、R² 与 RT60 |
| 噪声判废 | `GET /api/noise/{source_id}` | 测噪区间和动态范围 |
| 频段勾稽 | `GET /api/reconcile/{source_id}` | 频带、采样行守恒和拟合标差 |
| 复测归档 | `POST /api/runs`、`POST /api/runs/{id}/rerun` | 批次、摘要、复测与附件 |

[数据定义](docs/DATA-DICTIONARY.md)说明输入限制和计算边界。[深度登记](docs/DEPTH.md)列出样例与对应测试。
