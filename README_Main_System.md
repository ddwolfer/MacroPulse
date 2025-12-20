# AI 總經與預測市場分析系統 - 開發主控文件

## 1. 專案背景與目標

本專案源於對美股與加密貨幣（Crypto）投資的深度分析需求。傳統的投資分析往往受限於單一維度（只看價格或只看新聞），本系統旨在建立一個**由上而下（Top-Down）**的自動化分析框架。

### 核心目標：

- **自動化數據採集**：從聯準會、政府機構、預測市場抓取第一手數據。
- **多維度邏輯推理**：模擬不同領域專家的思考邏輯。
- **解決預期差**：透過 Polymarket 等即時數據，捕捉市場定價與實際數據之間的落差。
- **產出具備行動力的報告**：不只是數據堆砌，而是提供投資策略的參考。

## 2. 系統架構：多 Agent 協同模式

系統採用 **Async Multi-Agent** 模式。每個子 Agent 負責特定的專業領域，最後由主編 Agent 進行邏輯審核與總結。

### 數據流向 (Data Pipeline)

1. **Collectors (採集層)**：定時從 FRED, yfinance, Polymarket 抓取原始數據。
2. **Data Cache (暫存層)**：存儲 JSON 格式的原始數據，避免重複呼叫 API 浪費額度。
3. **Specialist Agents (專業分析層)**：
   - 讀取對應的數據片段。
   - 使用特定的 System Prompt 進行分析。
   - 產出結構化的「子報告」。
4. **Editor Agent (整合生成層)**：
   - 接收所有子報告。
   - 執行「矛盾檢索」與「觀點提煉」。
   - 生成最終的 Markdown 檔。

## 3. 開發路徑指引

在 Cursor 開發時，請務必按照以下順序進行，並參考對應的 .md 規格文件：

### Phase 0: 文件準備（已完成）
- ✅ 所有規格文件已就緒，請參閱 `SPEC_Project_Assessment.md` 了解完整文件清單

### Phase 1: 環境初始化
1. **環境初始化**：
   - 建立專案結構（參考下方目錄結構）
   - 配置 `.env` 檔案（參考 `SPEC_Configuration.md`）
   - 建立 `config.py`（參考 `SPEC_Configuration.md`）
   - 建立 `main.py` 骨架

### Phase 2: 實作數據採集器 (Collectors)
2. **實作數據採集器**：
   - 優先實作 Polymarket 與 FRED 數據抓取
   - **必讀文件**：`SPEC_API_Integrations.md`（API 端點、參數、錯誤處理）
   - **數據模型**：參考 `SPEC_Data_Models.md` 定義 Pydantic 模型
   - **錯誤處理**：參考 `SPEC_Error_Handling.md` 實作重試和降級機制

### Phase 3: 實作專業 Agent
3. **實作專業 Agent (循序漸進)**：
   - **Agent 規格書**（角色定位、核心邏輯）：
     - `Spec_Agent_Fed_Watcher.md` (貨幣政策)
     - `Spec_Agent_Data_Analyst.md` (經濟指標)
     - `Spec_Agent_Prediction_Specialist.md` (情緒與預測市場)
     - `Spec_Agent_Correlation_Expert.md` (資產連動)
   - **Prompt 模板**：參考 `SPEC_Prompt_Templates.md`（完整的 System Prompt 和 User Prompt）
   - **輸出模型**：參考 `SPEC_Data_Models.md`（Pydantic Schema 定義）

### Phase 4: 實作總結 Agent
4. **實作總結 Agent**：
   - 參閱 `Spec_Agent_Editor_In_Chief.md`（角色定位）
   - 參考 `SPEC_Prompt_Templates.md`（Editor Agent 的完整 Prompt）
   - 參考 `SPEC_Data_Models.md`（FinalReport 模型）

### Phase 5: 測試與優化
5. **測試與優化**：
   - 參考 `SPEC_Error_Handling.md` 確保錯誤處理完善
   - 參考 `AGENT.md` 的測試原則

## 4. 目錄結構參考

```
/macro-daily-robot
├── main.py                 # 入口點（Orchestrator）
├── config.py               # 配置管理（參考 SPEC_Configuration.md）
├── .env                     # 環境變數（參考 SPEC_Configuration.md）
├── .env.example            # 環境變數範本
├── /src
│   ├── /collectors         # 數據採集層 (I/O Bound)
│   │   ├── base_collector.py  # 統一的 Request 邏輯與重試機制
│   │   ├── polymarket_data.py # 處理 Gamma API（參考 SPEC_API_Integrations.md）
│   │   ├── fred_data.py       # 處理 FRED API（參考 SPEC_API_Integrations.md）
│   │   └── market_data.py     # 處理 yfinance（參考 SPEC_API_Integrations.md）
│   ├── /agents             # 邏輯分析層 (CPU/LLM Bound)
│   │   ├── base_agent.py      # 定義 LLM 調用介面（參考 AGENT.md）
│   │   ├── fed_agent.py       # 貨幣政策分析（參考 Spec_Agent_Fed_Watcher.md）
│   │   ├── econ_agent.py     # 經濟指標分析（參考 Spec_Agent_Data_Analyst.md）
│   │   ├── sentiment_agent.py # 預測市場分析（參考 Spec_Agent_Prediction_Specialist.md）
│   │   ├── correlation_agent.py # 資產連動分析（參考 Spec_Agent_Correlation_Expert.md）
│   │   └── editor_agent.py    # 報告總結（參考 Spec_Agent_Editor_In_Chief.md）
│   ├── /schema             # 數據定義層
│   │   └── models.py          # Pydantic 模型（參考 SPEC_Data_Models.md）
│   └── /utils              # 工具層
│       ├── logger.py          # 日誌格式化
│       ├── formatters.py      # Markdown 與數字格式化工具
│       └── cache.py           # 緩存管理（參考 SPEC_Error_Handling.md）
├── /data_cache             # 原始 JSON 緩存（參考 SPEC_Error_Handling.md）
├── /outputs                # 最終生成的 Markdown 報告
└── /test_scripts           # 測試腳本（參考 AGENT.md）
```

## 5. 關鍵規格文件索引

開發時請參考以下規格文件：

| 文件 | 用途 | 何時查看 |
|------|------|----------|
| `SPEC_Project_Assessment.md` | 專案文件完整性評估 | 了解整體文件結構 |
| `SPEC_API_Integrations.md` | API 整合詳細規格 | 開發 Collectors 時 |
| `SPEC_Data_Models.md` | 所有 Pydantic 模型定義 | 定義數據結構時 |
| `SPEC_Prompt_Templates.md` | LLM Prompt 完整模板 | 開發 Agent 時 |
| `SPEC_Configuration.md` | 配置管理規格 | 設定環境變數和配置時 |
| `SPEC_Error_Handling.md` | 錯誤處理和降級策略 | 實作錯誤處理時 |
| `AGENT.md` | 開發規範和最佳實踐 | 開發過程中隨時參考 |
