# MacroPulse - AI 總經與預測市場分析系統

> 多 Agent 協同分析框架，自動化總經與預測市場分析

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Development-yellow.svg)](TODO.md)

## 📖 專案簡介

MacroPulse 是一個基於 AI 的總經分析系統，採用**多 Agent 協同模式**，從上而下（Top-Down）自動化分析：

- 🏦 **貨幣政策分析**：聯準會決策、利率預期、美債殖利率曲線
- 📊 **經濟指標分析**：CPI、失業率、PMI 等指標趨勢
- 🎯 **預測市場情緒**：Polymarket 即時數據，捕捉市場定價
- 🔗 **資產連動分析**：跨資產相關係數、持倉風險評估

## 🏗️ 系統架構

```
MacroPulse/
├── main.py                 # 主程式入口
├── config.py               # 配置管理
├── .env.example            # 環境變數範本
├── src/
│   ├── collectors/         # 數據採集層
│   │   ├── polymarket_data.py
│   │   ├── fred_data.py
│   │   └── market_data.py
│   ├── agents/             # 專業分析層
│   │   ├── fed_agent.py
│   │   ├── econ_agent.py
│   │   ├── sentiment_agent.py
│   │   ├── correlation_agent.py
│   │   └── editor_agent.py
│   ├── schema/             # 數據模型層
│   │   └── models.py
│   └── utils/              # 工具層
│       ├── logger.py
│       ├── formatters.py
│       └── cache.py
├── data_cache/             # 數據緩存
├── outputs/                # 生成報告
└── test_scripts/           # 測試腳本
```

## 🚀 快速開始

### 1. 環境準備

**必要條件**：
- Python 3.10 或更高版本
- 有效的 API Keys（Google Gemini、FRED）

### 2. 安裝依賴

使用 `uv`（推薦）：
```bash
uv sync
```

或使用 `pip`：
```bash
pip install -r requirements.txt
```

### 3. 配置環境變數

複製 `.env.example` 為 `.env` 並填入你的 API Keys：
```bash
cp .env.example .env
```

編輯 `.env`：
```bash
# 必填
GEMINI_API_KEY=your-gemini-api-key
FRED_API_KEY=your-fred-api-key

# 可選（如需使用 OpenAI 作為備選）
OPENAI_API_KEY=sk-your-openai-key

# 可選
USER_PORTFOLIO=[{"symbol": "BTC-USD", "quantity": 1.5}]
```

### 4. 執行程式

使用 `uv`：
```bash
uv run python main.py
```

或直接執行：
```bash
python main.py
```

## 📋 開發進度

### ✅ Phase 1：環境初始化（已完成）

- [x] 建立專案結構
- [x] 配置管理 (`config.py`)
- [x] 環境變數範本 (`.env.example`)
- [x] 基礎工具模組 (`logger`, `formatters`, `cache`)
- [x] 主程式骨架 (`main.py`)

### ✅ Phase 2：數據採集器（已完成）

- [x] Polymarket 採集器 - Gamma API 預測市場數據
- [x] FRED 採集器 - 經濟指標數據（CPI, 失業率, NFP, PCE）
- [x] yfinance 採集器 - 美債殖利率、資產價格
- [x] 緩存機制整合（指數退避重試）

### ✅ Phase 3：專業分析 Agent（已完成）

- [x] **BaseAgent** - 基礎 Agent 類別，支援 Gemini API
- [x] **FedAgent** - 貨幣政策分析（殖利率曲線、鷹/鴿指數）
- [x] **EconAgent** - 經濟指標分析（軟著陸評分 0-10）
- [x] **SentimentAgent** - 預測市場情緒分析（市場焦慮度）
- [x] **CorrelationAgent** - 資產連動分析（相關係數、持倉風險）

### 🚧 Phase 4：報告生成（進行中）

- [ ] EditorAgent（報告總結與矛盾檢測）
- [ ] Markdown 格式化輸出

### ⏳ Phase 5：優化與自動化

- [ ] 優雅降級策略
- [ ] 定時執行設定
- [ ] 效能優化

詳細進度請查看 [TODO.md](TODO.md)

## 📚 文件索引

### 核心文件
- [README_Main_System.md](README_Main_System.md) - 專案總覽和開發路徑
- [AGENT.md](AGENT.md) - 開發規範和協作指引
- [TODO.md](TODO.md) - 開發進度清單

### 技術規格
- [SPEC_Configuration.md](SPEC_Configuration.md) - 配置管理規格
- [SPEC_API_Integrations.md](SPEC_API_Integrations.md) - API 整合規格
- [SPEC_Data_Models.md](SPEC_Data_Models.md) - 數據模型定義
- [SPEC_Prompt_Templates.md](SPEC_Prompt_Templates.md) - LLM Prompt 模板
- [SPEC_Error_Handling.md](SPEC_Error_Handling.md) - 錯誤處理策略

### Agent 規格
- [Spec_Agent_Fed_Watcher.md](Spec_Agent_Fed_Watcher.md) - 貨幣政策 Agent
- [Spec_Agent_Data_Analyst.md](Spec_Agent_Data_Analyst.md) - 經濟指標 Agent
- [Spec_Agent_Prediction_Specialist.md](Spec_Agent_Prediction_Specialist.md) - 預測市場 Agent
- [Spec_Agent_Correlation_Expert.md](Spec_Agent_Correlation_Expert.md) - 資產連動 Agent
- [Spec_Agent_Editor_In_Chief.md](Spec_Agent_Editor_In_Chief.md) - 報告總結 Agent

## 🛠️ 技術棧

- **語言**：Python 3.10+
- **配置管理**：Pydantic Settings
- **HTTP 請求**：httpx (async)
- **數據處理**：pandas, numpy
- **LLM**：Google Gemini Flash (Primary) / OpenAI GPT-4 (Backup)
- **金融數據**：yfinance, FRED API, Polymarket Gamma API

## 📝 開發規範

請在開發前閱讀：
- 代碼風格：遵循 [AGENT.md](AGENT.md) 的規範
- 錯誤處理：參考 [SPEC_Error_Handling.md](SPEC_Error_Handling.md)
- Commit 規範：使用繁體中文（新增、修正、文件、重構、維護、優化）

## 🐛 錯誤記錄

已解決的問題和技術陷阱記錄在 [error_log.md](error_log.md)

## 📄 License

MIT License

## 👥 貢獻者

MacroPulse Team

---

**版本**：v0.3.0  
**狀態**：開發中（Phase 3 完成）  
**最後更新**：2026-01-09