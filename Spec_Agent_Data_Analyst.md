# Agent 規格書：經濟指標分析師 (The Data Analyst)

## 1. 角色定位

模擬一位總體經濟學家，擅長從硬數據（Hard Data）中找出經濟循環的拐點。

## 2. 核心 Input 數據

- **通膨數據**：CPI (YoY, MoM), PCE 核心物價指數。
- **就業數據**：NFP 非農就業人數、失業率、初請失業金。
- **領先指標**：ISM 製造業/服務業 PMI。

## 3. 開發重點 (針對 Cursor)

### A. 數據抓取 (src/collectors/econ_data.py)

- 建議使用 FRED API (需申請 API Key，免費)。
- **詳細規格**：參考 `SPEC_API_Integrations.md` 的 FRED API 章節
- **必要系列代碼**：
  - `CPIAUCSL` (CPI)
  - `UNRATE` (失業率)
  - `PAYEMS` (非農)
  - `PCEPI` (PCE 物價指數)
  - `PMI` (ISM 製造業 PMI)
- **數據模型**：參考 `SPEC_Data_Models.md` 的 `FREDSeries` 和 `FREDObservation` 模型

### B. 分析邏輯 (src/agents/econ_agent.py)

- **完整 Prompt 模板**：參考 `SPEC_Prompt_Templates.md` 的 Economic Data Analyst 章節
- **核心邏輯**：數據是否支持「軟著陸」？
- **對比分析**：將「當前值」與「市場預期值」對比。
- **結構化輸出**：參考 `SPEC_Data_Models.md` 的 `EconomicAnalysisOutput` 模型
  - `soft_landing_score`: 經濟景氣評分 (0-10)
  - `inflation_trend`: 通膨趨勢（上升/下降/穩定）
  - `employment_status`: 就業狀況（強勁/疲弱/穩定）
  - `key_indicators`: 關鍵指標數值字典
  - `summary`: 經濟狀況總結
  - `confidence`: 信心指數 (0.0-1.0)

### C. 錯誤處理

- **錯誤處理策略**：參考 `SPEC_Error_Handling.md`
- 如果 FRED API 失敗，嘗試使用緩存數據
- 如果部分指標缺失，降低 confidence 並在 summary 中說明

## 4. 技術注意事項

由於經濟數據發布有特定時間，Agent 應具備「時效性意識」，例如：如果今天是非農公布日，該 Agent 的權重要自動提升。
