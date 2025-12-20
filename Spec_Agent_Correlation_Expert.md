# Agent 規格書：資產連動專家 (The Correlation Expert)

## 1. 角色定位

模擬一位量化交易員或跨資產經理人，負責把宏觀數據翻譯成對美股 (SPX/NDX) 與加密貨幣 (BTC/ETH) 的具體影響。

## 2. 核心 Input 數據

- **價格數據**：BTC-USD, ETH-USD, QQQ, SPY, DXY (美元指數)。
- **鏈上數據 (可選)**：穩定幣流入量、交易所餘額。
- **用戶持倉 (你的需求)**：傳入你目前持有的標的清單。

## 3. 開發重點 (針對 Cursor)

### A. 數據處理 (src/collectors/market_data.py)

- 使用 `yfinance` 獲取資產 7 天的價格走勢。
- 使用 `pandas` 計算資產間的 `correlation_matrix` (相關係數矩陣)。

### B. 分析邏輯 (src/agents/correlation_agent.py)

- **核心分析**：「當前環境下，BTC 是跟著黃金走 (避險)，還是跟著納斯達克走 (風險資產)？」
- **風險預警**：如果美元指數 (DXY) 強勢上漲，對持有標的的負面影響有多大？

## 4. 輸出範例

「目前 BTC 與 DXY 呈現強負相關 (-0.85)，近期美元的走強可能是壓制 Crypto 反彈的主因。建議關注今日美元指數的 105 壓力位。」
