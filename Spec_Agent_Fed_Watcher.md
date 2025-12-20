# Agent 規格書：貨幣政策分析師 (The Fed Watcher)

## 1. 角色定位

模擬一位專精於「固定收益商品」與「聯準會行為」的資深策略師。

## 2. 核心 Input 數據

- **FedWatch Tool 數據**：下一次 FOMC 會議降息/升息的機率分布。
- **美債殖利率**：2 年期 (敏感度高) 與 10 年期 (經濟預期) 數據。
- **官員言論 (Fed Speak)**：最近一週重要官員的偏鷹/偏鴿立場摘要。

## 3. 開發重點 (針對 Cursor)

### A. 數據抓取 (src/collectors/fed_data.py)

- 使用 `yfinance` 抓取 `^IRX` (3M Bill), `^FVX` (5Y), `^TNX` (10Y)。
- 計算「殖利率曲線倒掛」狀況（10Y - 2Y）。
- **詳細規格**：參考 `SPEC_API_Integrations.md` 的 yfinance 章節
- **數據模型**：參考 `SPEC_Data_Models.md` 的 `TreasuryYield` 模型

### B. LLM 分析邏輯 (src/agents/fed_agent.py)

- **完整 Prompt 模板**：參考 `SPEC_Prompt_Templates.md` 的 Fed Agent 章節
- **System Prompt 要點**：
  - 「你必須專注於聯準會對於『中性利率』的態度。」
  - 「分析市場定價是否過於樂觀（例如：Polymarket 預期降息 3 次，但官員暗示只會降 1 次）。」
- **輸出結構 (Schema)**：參考 `SPEC_Data_Models.md` 的 `FedAnalysisOutput` 模型
  - `tone_index`: (Float, -1.0 到 1.0, -1 代表極鴿, 1 代表極鷹)
  - `key_risks`: 列表（3-5 個）
  - `summary`: 200 字以內的專業解讀
  - `confidence`: 信心指數 (0.0-1.0)
  - `yield_curve_status`: 殖利率曲線狀態
  - `next_fomc_probability`: 下次 FOMC 降息機率（可選）

### C. 錯誤處理

- **錯誤處理策略**：參考 `SPEC_Error_Handling.md`
- 如果數據獲取失敗，使用緩存數據（如果存在）
- 如果 LLM 分析失敗，返回空結構，不中斷整體流程

## 4. 期待產出範例

「當前美債 2Y 殖利率大幅下行，顯示市場正在定價 1 月份的預防性降息。然而 FedWatch 顯示機率僅為 40%，這存在潛在的波動風險...」
