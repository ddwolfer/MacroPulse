# 專案開發進度清單 (TODO List)

## 📋 Phase 0: 文件準備（已完成 ✅）

- [x] **0.1 專案文件評估**
  - [x] 完成專案文件完整性評估（`SPEC_Project_Assessment.md`）
- [x] **0.2 技術規格文件**
  - [x] 創建 API 整合規格（`SPEC_API_Integrations.md`）
  - [x] 創建數據模型規格（`SPEC_Data_Models.md`）
  - [x] 創建 Prompt 模板規格（`SPEC_Prompt_Templates.md`）
  - [x] 創建配置管理規格（`SPEC_Configuration.md`）
  - [x] 創建錯誤處理規格（`SPEC_Error_Handling.md`）
- [x] **0.3 現有文件更新**
  - [x] 更新 `README_Main_System.md` 加入新文件引用
  - [x] 更新 `AGENT.md` 加入新文件索引
  - [x] 更新所有 `Spec_Agent_*.md` 加入詳細技術規格引用

## 📅 第一階段：環境初始化與專案骨架（✅ 已完成）

- [x] **1.1 專案結構建立**
  - [x] 按照 `README_Main_System.md` 建立資料夾結構。
  - [x] 建立 `.gitignore` (排除 `__pycache__`, `.env`, `data_cache/`, `outputs/`)。
  - [x] 建立所有必要的 `__init__.py` 檔案。
- [x] **1.2 配置管理**
  - [x] 參考 `SPEC_Configuration.md` 建立 `config.py` 使用 `pydantic-settings` 管理配置。
  - [x] 參考 `SPEC_Configuration.md` 準備 `.env.example` 範本檔案。
  - [x] 實作配置驗證函數 `validate_config()`。
  - [x] 實作目錄初始化 `ensure_directories()`。
- [x] **1.3 核心入口實作**
  - [x] 撰寫 `main.py` 的非同步 (async) 執行邏輯。
  - [x] 實作基本的日誌 (Logging) 系統 (`src/utils/logger.py`)。
  - [x] 實作格式化工具 (`src/utils/formatters.py`)。
  - [x] 實作緩存管理器 (`src/utils/cache.py`)。
- [x] **1.4 依賴管理**
  - [x] 建立 `requirements.txt`。
  - [x] 建立 `pyproject.toml`。
- [x] **1.5 文件更新**
  - [x] 更新 `README.md` 為完整的專案介紹。

## 📊 第二階段：數據採集器 (Collectors) 實作（✅ 已完成）

- [x] **2.1 數據模型定義** (`src/schema/models.py`)
  - [x] Collector 層模型（Polymarket, FRED, Treasury, Asset）
  - [x] Agent 輸出模型（Fed, Economic, Prediction, Correlation）
  - [x] Editor 輸出模型（FinalReport）
  - [x] 工具模型（UserPortfolio, AgentError）
- [x] **2.2 基礎採集器** (`src/collectors/base_collector.py`)
  - [x] HTTP 請求邏輯
  - [x] 指數退避重試機制
  - [x] 緩存管理整合
  - [x] 錯誤處理
- [x] **2.3 Polymarket 採集器** (`src/collectors/polymarket_data.py`)
  - [x] Gamma API 呼叫
  - [x] 數據過濾（交易量門檻）
  - [x] 緩存機制（TTL: 1 小時）
- [x] **2.4 FRED 經濟數據採集器** (`src/collectors/fred_data.py`)
  - [x] FRED API 串接
  - [x] 多系列並行採集
  - [x] 緩存機制（TTL: 24 小時）
- [x] **2.5 金融市場採集器** (`src/collectors/market_data.py`)
  - [x] yfinance 美債殖利率
  - [x] 資產價格歷史
  - [x] 相關係數計算
  - [x] 用戶持倉支援
  - [x] 緩存機制（TTL: 15 分鐘）
- [x] **2.6 測試腳本**
  - [x] `test_scripts/test_collectors.py`
- [x] **2.7 主程式整合**
  - [x] 更新 `main.py` 使用採集器
  - [x] 並行採集（asyncio.gather）
  - [x] 異常處理和降級

## 🧠 第三階段：專業分析 Agent 實作

- [x] **3.1 基礎 Agent 類別** (`src/agents/base_agent.py`)
  - [x] 定義所有 Agent 的共同介面與 LLM 呼叫邏輯。
  - [x] 支援 Gemini API（新舊版本兼容）
  - [x] Prompt 渲染機制
  - [x] JSON 解析和修復
  - [x] 錯誤處理和重試機制
  - [x] 輸出驗證（Pydantic）
- [ ] **3.2 貨幣政策 Agent** (`src/agents/fed_agent.py`)
  - [ ] 參考 `Spec_Agent_Fed_Watcher.md` 了解角色定位。
  - [ ] 參考 `SPEC_Prompt_Templates.md` 實作完整的 System Prompt 和 User Prompt。
  - [ ] 參考 `SPEC_Data_Models.md` 定義 `FedAnalysisOutput` 模型。
  - [ ] 實作 LLM 呼叫邏輯（參考 `AGENT.md` 的 BaseAgent 模式）。
  - [ ] 參考 `SPEC_Error_Handling.md` 實作錯誤處理。
- [ ] **3.3 經濟指標 Agent** (`src/agents/econ_agent.py`)
  - [ ] 參考 `Spec_Agent_Data_Analyst.md` 了解角色定位。
  - [ ] 參考 `SPEC_Prompt_Templates.md` 實作完整的 Prompt。
  - [ ] 參考 `SPEC_Data_Models.md` 定義 `EconomicAnalysisOutput` 模型。
  - [ ] 實作軟著陸評分邏輯。
- [ ] **3.4 預測市場 Agent** (`src/agents/sentiment_agent.py`)
  - [ ] 參考 `Spec_Agent_Prediction_Specialist.md` 了解角色定位。
  - [ ] 參考 `SPEC_Prompt_Templates.md` 實作完整的 Prompt。
  - [ ] 參考 `SPEC_Data_Models.md` 定義 `PredictionAnalysisOutput` 模型。
  - [ ] 實作市場焦慮度量化邏輯。
- [ ] **3.5 資產連動 Agent** (`src/agents/correlation_agent.py`)
  - [ ] 參考 `Spec_Agent_Correlation_Expert.md` 了解角色定位。
  - [ ] 參考 `SPEC_Prompt_Templates.md` 實作完整的 Prompt。
  - [ ] 參考 `SPEC_Data_Models.md` 定義 `CorrelationAnalysisOutput` 模型。
  - [ ] 實作相關係數計算和風險預警邏輯。
  - [ ] 加入用戶自定義持倉標的的分析邏輯（參考 `SPEC_Configuration.md` 的 `USER_PORTFOLIO`）。

## ✍️ 第四階段：總結與報告生成 (Editor)

- [ ] **4.1 主編 Agent 實作** (`src/agents/editor_agent.py`)
  - [ ] 參考 `Spec_Agent_Editor_In_Chief.md` 了解角色定位。
  - [ ] 參考 `SPEC_Prompt_Templates.md` 實作完整的 Editor Prompt。
  - [ ] 參考 `SPEC_Data_Models.md` 定義 `FinalReport` 模型。
  - [ ] 實作多份子報告的整合邏輯。
  - [ ] 實作「衝突偵測」與「重點提煉」邏輯。
  - [ ] 實作信心指數計算（所有 Agent 的平均值）。
- [ ] **4.2 Markdown 格式化器**
  - [ ] 確保最終輸出符合美觀的 Markdown 排版（包含表格與標題）。
  - [ ] 實作報告檔案命名規則（例如：`report_YYYY-MM-DD_HH-MM.md`）。

## 🚀 第五階段：優化與自動化

- [ ] **5.1 錯誤處理與重試機制**
  - [ ] 參考 `SPEC_Error_Handling.md` 實作指數退避 (Exponential Backoff) 重試。
  - [ ] 實作優雅降級策略（Agent 失敗時不中斷整體流程）。
  - [ ] 實作錯誤日誌記錄和統計。
- [ ] **5.2 定時執行設定**
  - [ ] 設定本地 Cron job 或 GitHub Actions 自動運行腳本。
- [ ] **5.3 效能優化**
  - [ ] 確保所有 I/O 密集型任務皆為非同步執行。
- [ ] **5.4 (進階) 視覺化擴充**
  - [ ] 考慮產出簡單的趨勢圖表並嵌入 Markdown。
