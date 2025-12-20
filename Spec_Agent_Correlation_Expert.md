# Agent 規格書：資產連動專家 (The Correlation Expert)

## 1. 角色定位

模擬一位量化交易員或跨資產經理人，負責把宏觀數據翻譯成對美股 (SPX/NDX) 與加密貨幣 (BTC/ETH) 的具體影響。

## 2. 核心 Input 數據

- **價格數據**：BTC-USD, ETH-USD, QQQ, SPY, DXY (美元指數)。
- **鏈上數據 (可選)**：穩定幣流入量、交易所餘額。
- **用戶持倉 (你的需求)**：傳入你目前持有的標的清單。

## 3. 開發重點 (針對 Cursor)

### A. 數據處理 (src/collectors/market_data.py)

- **詳細規格**：參考 `SPEC_API_Integrations.md` 的 yfinance 章節
- 使用 `yfinance` 獲取資產 7 天的價格走勢（天數可配置，見 `SPEC_Configuration.md`）
- 使用 `pandas` 計算資產間的 `correlation_matrix` (相關係數矩陣)
- **必要資產**：BTC-USD, ETH-USD, QQQ, SPY, DXY (美元指數)
- **數據模型**：參考 `SPEC_Data_Models.md` 的 `AssetPrice` 和 `AssetPriceHistory` 模型

### B. 分析邏輯 (src/agents/correlation_agent.py)

- **完整 Prompt 模板**：參考 `SPEC_Prompt_Templates.md` 的 Correlation Expert 章節
- **核心分析**：「當前環境下，BTC 是跟著黃金走 (避險)，還是跟著納斯達克走 (風險資產)？」
- **風險預警**：如果美元指數 (DXY) 強勢上漲，對持有標的的負面影響有多大？
- **結構化輸出**：參考 `SPEC_Data_Models.md` 的 `CorrelationAnalysisOutput` 模型
  - `correlation_matrix`: 資產間相關係數矩陣（字典格式）
  - `risk_warnings`: 風險預警列表
  - `portfolio_impact`: 對用戶持倉的影響分析（如果提供持倉）
  - `summary`: 連動分析總結
  - `confidence`: 信心指數 (0.0-1.0)

### C. 用戶持倉支援

- 如果提供用戶持倉（透過 `SPEC_Configuration.md` 的 `USER_PORTFOLIO`），分析對持倉的具體影響
- **持倉模型**：參考 `SPEC_Data_Models.md` 的 `UserPortfolio` 模型

### D. 錯誤處理

- **錯誤處理策略**：參考 `SPEC_Error_Handling.md`
- 如果部分資產數據獲取失敗，使用可用數據繼續分析，降低 confidence
- 如果相關係數計算失敗，返回空矩陣，在 summary 中說明

## 4. 輸出範例

「目前 BTC 與 DXY 呈現強負相關 (-0.85)，近期美元的走強可能是壓制 Crypto 反彈的主因。建議關注今日美元指數的 105 壓力位。」
