# Agent 規格書：總結與主編 (Editor-in-Chief)

## 1. 角色定位

模擬投資銀行（如高盛或大摩）的研究部門總監，負責最後的品質把關與報告撰寫。

## 2. 核心 Input 數據

來自 `Fed_Watcher`, `Data_Analyst`, `Prediction_Specialist`, `Correlation_Expert` 的四份 Markdown 分析草稿。

## 3. 開發重點 (針對 Cursor)

### A. 整合邏輯 (src/agents/editor_agent.py)

- **完整 Prompt 模板**：參考 `SPEC_Prompt_Templates.md` 的 Editor-in-Chief 章節
- **邏輯衝突檢查**：如果 Data Agent 說經濟過熱，但 Fed Agent 說要大降息，主編必須在報告中指出這種「市場不理性」或「邏輯背離」。
- **階層化撰寫**：
  - **TL;DR (Too Long; Didn't Read)**：三句話總結今日核心（最多 200 字）。
  - **深度亮點**：從 Polymarket 數據中挑出最令人驚訝的發現（3-5 個）。
  - **投資建議**：針對用戶持倉的宏觀風險建議（最多 1000 字）。
- **輸入數據**：接收四個 Agent 的輸出（`FedAnalysisOutput`, `EconomicAnalysisOutput`, `PredictionAnalysisOutput`, `CorrelationAnalysisOutput`）

### B. 輸出格式

- **數據模型**：參考 `SPEC_Data_Models.md` 的 `FinalReport` 模型
- **排版風格**：
  - 嚴格要求輸出標準 Markdown，包含表格、加粗重點、以及有序列表。
  - 加入「信心指數」(Confidence Score)，告訴用戶今日分析的確定程度（所有 Agent 的平均值）。
  - 如果檢測到邏輯衝突，在 `conflicts` 欄位中列出。

### C. 錯誤處理

- **錯誤處理策略**：參考 `SPEC_Error_Handling.md`
- 如果部分 Agent 失敗，在報告中標註「該分析暫時無法取得」，但不中斷報告生成
- 如果所有 Agent 都失敗，返回錯誤報告而非空報告

## 4. 關鍵 Prompt 指令

「你是一位挑惕的研究總監。你的任務是刪除冗餘資訊，只保留對投資決策有幫助的洞察。如果子 Agent 給出的資訊太籠統，請在報告中提出質疑。」

**完整 Prompt 請參考**：`SPEC_Prompt_Templates.md` 的 Editor-in-Chief 章節
