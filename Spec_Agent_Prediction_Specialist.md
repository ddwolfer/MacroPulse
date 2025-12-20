# Agent 規格書：預測市場分析師 (The Prediction Specialist)

## 1. 角色定位

模擬一位「地下金融觀測員」與「行為金融學家」，透過 Polymarket 的真實金流來捕捉大眾的情緒與尚未公開的訊息。

## 2. 核心 Input 數據

**Polymarket API (Gamma API)**：
- **分類**：Macro, Politics, Crypto
- **關鍵指標**：Market Title, Current Price (Probability), 24h Volume, 7d Price Change

## 3. 開發重點 (針對 Cursor)

### A. API 實作 (src/collectors/polymarket_data.py)

- 使用 Endpoint: `https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=20`
- **篩選邏輯**：優先抓取交易量（Volume）大於 $100,000 的盤口。

### B. 分析邏輯 (src/agents/sentiment_agent.py)

- **System Prompt**：
  - 「你是預測市場專家，你的任務是找出機率突然發生劇烈變動的盤口。」
  - 「分析政治事件（如：某項法案通過機率）對金融市場的潛在外部性影響。」
- **情緒量化**：將 Polymarket 的機率變動轉化為「市場焦慮度」或「樂觀度」。

## 4. 優勢

這是本專案最獨特的部分，開發時應強調「預測機率」與「傳統新聞」的對比。
