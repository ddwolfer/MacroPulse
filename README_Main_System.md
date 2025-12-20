AI 總經與預測市場分析系統 - 開發主控文件1. 專案背景與目標本專案源於對美股與加密貨幣（Crypto）投資的深度分析需求。傳統的投資分析往往受限於單一維度（只看價格或只看新聞），本系統旨在建立一個**由上而下（Top-Down）**的自動化分析框架。核心目標：自動化數據採集： 從聯準會、政府機構、預測市場抓取第一手數據。多維度邏輯推理： 模擬不同領域專家的思考邏輯。解決預期差： 透過 Polymarket 等即時數據，捕捉市場定價與實際數據之間的落差。產出具備行動力的報告： 不只是數據堆砌，而是提供投資策略的參考。2. 系統架構：多 Agent 協同模式系統採用 Async Multi-Agent 模式。每個子 Agent 負責特定的專業領域，最後由主編 Agent 進行邏輯審核與總結。數據流向 (Data Pipeline)Collectors (採集層): 定時從 FRED, yfinance, Polymarket 抓取原始數據。Data Cache (暫存層): 存儲 JSON 格式的原始數據，避免重複呼叫 API 浪費額度。Specialist Agents (專業分析層):讀取對應的數據片段。使用特定的 System Prompt 進行分析。產出結構化的「子報告」。Editor Agent (整合生成層):接收所有子報告。執行「矛盾檢索」與「觀點提煉」。生成最終的 Markdown 檔。3. 開發路徑指引在 Cursor 開發時，請務必按照以下順序進行，並參考對應的 .md 規格文件：環境初始化： 建立專案結構、配置 .env 與 main.py 骨架。實作數據採集器 (Collectors)： 優先實作 Polymarket 與 FRED 數據抓取。實作專業 Agent (循序漸進)：參閱 Spec_Agent_Fed_Watcher.md (貨幣政策)參閱 Spec_Agent_Data_Analyst.md (經濟指標)參閱 Spec_Agent_Prediction_Specialist.md (情緒與預測市場)參閱 Spec_Agent_Correlation_Expert.md (資產連動)實作總結 Agent： 參閱 Spec_Agent_Editor_In_Chief.md。4. 目錄結構參考/macro-daily-robot
├── main.py                 # 入口點
├── config.py               # 密鑰管理
├── /src
│   ├── /collectors         # 負責 Requests/API
│   ├── /agents             # 負責 LLM Logic
│   └── /schema             # 負責 Pydantic Models (數據結構)
├── /data_cache             # 原始 JSON
└── /outputs                # 最終 Markdown
