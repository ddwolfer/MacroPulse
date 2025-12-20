# 專案開發進度清單 (TODO List)

## 📅 第一階段：環境初始化與專案骨架

- [ ] **1.1 專案結構建立**
  - [ ] 按照 `README_Main_System.md` 建立資料夾結構。
  - [ ] 建立 `.gitignore` (排除 `__pycache__`, `.env`, `data_cache/`, `outputs/`)。
- [ ] **1.2 配置管理**
  - [ ] 建立 `config.py` 使用 `pydantic-settings` 或 `python-dotenv` 管理 API Keys。
  - [ ] 準備 `.env` 範本檔案 (包含 OpenAI/Gemini, FRED API, Polymarket API 等)。
- [ ] **1.3 核心入口實作**
  - [ ] 撰寫 `main.py` 的非同步 (async) 執行邏輯。
  - [ ] 實作基本的日誌 (Logging) 系統。

## 📊 第二階段：數據採集器 (Collectors) 實作

- [ ] **2.1 Polymarket 採集器** (`src/collectors/polymarket_data.py`)
  - [ ] 實作 Gamma API 呼叫，抓取 Macro 類別活躍盤口。
  - [ ] 實作數據過濾（交易量門檻、機率變動計算）。
- [ ] **2.2 FRED 經濟數據採集器** (`src/collectors/econ_data.py`)
  - [ ] 串接 FRED API 抓取 CPI, 失業率, PMI 等指標。
- [ ] **2.3 金融市場採集器** (`src/collectors/market_data.py`)
  - [ ] 使用 `yfinance` 抓取美債殖利率 (2Y, 10Y)。
  - [ ] 抓取主要標的 (BTC, ETH, QQQ, SPY) 價格歷史。
- [ ] **2.4 緩存機制實作**
  - [ ] 實作將原始數據存入 `data_cache/` 的功能，避免重複請求。

## 🧠 第三階段：專業分析 Agent 實作

- [ ] **3.1 基礎 Agent 類別** (`src/agents/base_agent.py`)
  - [ ] 定義所有 Agent 的共同介面與 LLM 呼叫邏輯。
- [ ] **3.2 貨幣政策 Agent** (`src/agents/fed_agent.py`)
  - [ ] 實作對應 `Spec_Agent_Fed_Watcher.md` 的 Prompt。
  - [ ] 定義 Pydantic 輸出模型（鷹/鴿指數）。
- [ ] **3.3 經濟指標 Agent** (`src/agents/econ_agent.py`)
  - [ ] 實作對應 `Spec_Agent_Data_Analyst.md` 的 Prompt。
- [ ] **3.4 預測市場 Agent** (`src/agents/sentiment_agent.py`)
  - [ ] 實作對應 `Spec_Agent_Prediction_Specialist.md` 的 Prompt。
- [ ] **3.5 資產連動 Agent** (`src/agents/correlation_agent.py`)
  - [ ] 實作對應 `Spec_Agent_Correlation_Expert.md` 的 Prompt。
  - [ ] 加入用戶自定義持倉標的的分析邏輯。

## ✍️ 第四階段：總結與報告生成 (Editor)

- [ ] **4.1 主編 Agent 實作** (`src/agents/editor_agent.py`)
  - [ ] 實作多份子報告的整合 Prompt。
  - [ ] 實作「衝突偵測」與「重點提煉」邏輯。
- [ ] **4.2 Markdown 格式化器**
  - [ ] 確保最終輸出符合美觀的 Markdown 排版（包含表格與標題）。

## 🚀 第五階段：優化與自動化

- [ ] **5.1 錯誤處理與重試機制**
  - [ ] 針對 API 呼叫實作指數退避 (Exponential Backoff) 重試。
- [ ] **5.2 定時執行設定**
  - [ ] 設定本地 Cron job 或 GitHub Actions 自動運行腳本。
- [ ] **5.3 效能優化**
  - [ ] 確保所有 I/O 密集型任務皆為非同步執行。
- [ ] **5.4 (進階) 視覺化擴充**
  - [ ] 考慮產出簡單的趨勢圖表並嵌入 Markdown。
