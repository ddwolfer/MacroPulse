# AI 協作指引 (Agent Collaboration Guide)

本專案是一個基於多 Agent 架構的總經與預測市場分析系統（Macro & Prediction Market Analysis）。以下是與 Cursor AI 協作時的最高準則、架構規範與開發流程。

## 📚 專案文件導覽

請在進行任何開發任務前，務必優先閱讀以下文件以維持邏輯一致性：

### 核心管理文件（必讀）

| 檔案 | 用途 | 何時查看 |
|------|------|----------|
| `README_Main_System.md` | 專案總覽、系統架構、數據流向總圖 | 初次接觸專案或修改整體架構時 |
| `SPEC_Project_Assessment.md` | 專案文件完整性評估報告 | 了解文件結構和開發優先順序 |
| `TODO.md` | 當前開發進度、優先級、已完成功能 | 每次開始新任務前，需更新狀態 |
| `config.py` | 核心配置、API 金鑰管理、路徑定義 | 需要新增 API 或修改全域設定時 |

### Agent 開發規格（邏輯細節）

| 檔案 | 負責領域 | 核心技術點 |
|------|----------|------------|
| `Spec_Agent_Fed_Watcher.md` | 貨幣政策與利率分析 | 聯準會預期差、美債殖利率曲線 |
| `Spec_Agent_Data_Analyst.md` | 經濟指標與通膨解讀 | FRED API, 軟/硬著陸邏輯判斷 |
| `Spec_Agent_Prediction_Specialist.md` | Polymarket 情緒監測 | Gamma API, 預測市場機率捕捉 |
| `Spec_Agent_Correlation_Expert.md` | 資產連動與持倉分析 | 跨資產相關係數、持倉曝險分析 |
| `Spec_Agent_Editor_In_Chief.md` | 報告總結與邏輯審核 | 矛盾檢測、專業投研風格撰寫 |

### 技術規格文件（開發必讀）

| 檔案 | 用途 | 何時查看 |
|------|------|----------|
| `SPEC_API_Integrations.md` | API 端點、參數、認證、錯誤處理 | 開發 Collectors 時 |
| `SPEC_Data_Models.md` | 所有 Pydantic 模型的完整定義 | 定義數據結構時 |
| `SPEC_Prompt_Templates.md` | 所有 Agent 的完整 Prompt 模板 | 開發 Agent 分析邏輯時 |
| `SPEC_Configuration.md` | 環境變數、配置管理、.env 範本 | 設定專案環境時 |
| `SPEC_Error_Handling.md` | 錯誤處理、重試機制、降級策略 | 實作錯誤處理時 |

### 開發輔助（除錯必看）

| 檔案 | 用途 | 何時查看 |
|------|------|----------|
| `error_log.md` | 已解決的技術問題、根本原因分析 (Root Cause Analysis)、API 陷阱記錄 | 遇到類似錯誤時、解決問題後記錄 |

---

## 📖 文件閱讀順序建議

### 初次接觸專案
1. `README_Main_System.md` - 了解專案整體架構
2. `SPEC_Project_Assessment.md` - 了解文件結構
3. `AGENT.md` - 了解開發規範

### 開始開發前
1. `SPEC_Configuration.md` - 設定環境和配置
2. `SPEC_API_Integrations.md` - 了解 API 規格
3. `SPEC_Data_Models.md` - 了解數據結構

### 開發 Collectors 時
1. `SPEC_API_Integrations.md` - API 詳細規格
2. `SPEC_Data_Models.md` - Collector 層數據模型
3. `SPEC_Error_Handling.md` - 錯誤處理和緩存

### 開發 Agent 時
1. `Spec_Agent_*.md` - Agent 角色定位和邏輯
2. `SPEC_Prompt_Templates.md` - 完整的 Prompt 模板
3. `SPEC_Data_Models.md` - Agent 輸出模型
4. `SPEC_Error_Handling.md` - Agent 錯誤處理

### 遇到錯誤時
1. `error_log.md` - 檢查是否有類似問題的解決方案
2. `SPEC_Error_Handling.md` - 了解錯誤處理策略和降級機制
3. 相關的 API 或 Agent 規格文件 - 確認實作是否符合規格

## 💻 代碼風格規範

### 語言與編碼標準

- **註解與文檔字串 (Docstrings)**：統一使用繁體中文。
- **命名規範**：
  - 變數與函數：英文 `snake_case`（例如：`fetch_macro_events`）。
  - 類別名稱：英文 `PascalCase`（例如：`PolymarketCollector`）。
  - 常數：全大寫 `SCREAMING_SNAKE_CASE`。
- **檔案編碼**：UTF-8（無 BOM），LF 換行符。

### 非同步 Python 慣例

本專案高度依賴非同步 I/O，請遵循以下模式：

```python
# ✅ 推薦寫法：結合 Pydantic 與非同步異常處理
from typing import List, Optional
from pydantic import BaseModel

class MarketData(BaseModel):
    title: str
    probability: float

async def fetch_prediction_data(category: str) -> List[MarketData]:
    """
    獲取預測市場數據並驗證格式
    
    Args:
        category: 市場類別
        
    Returns:
        List[MarketData]: 經過驗證的數據列表
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BASE_URL}/markets", params={"q": category})
            response.raise_for_status()
            raw_data = response.json()
            
            # 使用 Pydantic 進行數據解析與驗證
            return [MarketData(**item) for item in raw_data]
            
    except httpx.HTTPStatusError as e:
        logger.error(f"API 回傳錯誤狀態: {e.response.status_code}")
        return []
    except Exception as e:
        logger.error(f"未預期的錯誤: {str(e)}")
        return []
```

### 類型提示 (Type Hints)

強烈建議使用 Python 類型提示（Type Hints）。所有 Agent 的分析函數必須明確定義傳入與回傳的 Schema。

## 🗂️ 專案架構與設計模式

### 模組職責劃分 (Modularization)

```
macro-daily-robot/
├── main.py                 # Orchestrator：負責 async 任務編排與流程管理
├── config.py               # Settings：基於 Pydantic Settings 的配置管理
├── src/
│   ├── collectors/         # 數據採集層 (I/O Bound)
│   │   ├── base_collector.py  # 統一的 Request 邏輯與重試機制
│   │   ├── polymarket_data.py # 處理 Gamma API
│   │   └── fred_data.py       # 處理 FRED API
│   ├── agents/             # 邏輯分析層 (CPU/LLM Bound)
│   │   ├── base_agent.py      # 定義 LLM 調用介面與模板渲染
│   │   ├── fed_agent.py       # 利率與政策邏輯
│   │   └── editor_agent.py    # 總結與格式化
│   ├── schema/             # 數據定義層
│   │   └── models.py          # 統一的 Pydantic 模型定義
│   └── utils/              # 工具層
│       ├── logger.py          # 日誌格式化
│       └── formatters.py      # Markdown 與數字格式化工具
├── data_cache/             # 暫存原始 JSON (快取機制)
└── outputs/                # 最終生成的 Markdown 報告
```

### 核心設計模式

- **Orchestrator Pattern**：`main.py` 作為指揮官，不執行具體業務，僅負責啟動非同步任務 (`asyncio.gather`)。
- **Strategy Pattern**：不同的 Agent 實現 `BaseAgent` 的 `analyze()` 方法，讓分析邏輯可替換。
- **Cache-Aside Pattern**：採集器優先讀取 `data_cache/` 中未過期的 JSON，減少對外部 API 的負擔。

## 🔧 開發工作流程

### 新增功能/Agent 時

1. **更新 TODO.md**：標記當前正在開發的任務與優先級。
2. **定義 Schema**：在 `src/schema/` 中定義數據模型，確保資料流穩定。
3. **開發 Collector**：實作數據抓取腳本，並進行單體測試確保 JSON 結構正確。
4. **開發 Agent**：撰寫分析邏輯，並使用 Mock 數據驗證 Prompt 輸出的穩定性。
5. **整合與輸出**：在 `main.py` 中掛載新 Agent，並測試報告生成。

### 遇到錯誤時

1. **查看 `error_log.md`**：先檢查是否有類似問題的解決方案，避免重複踩坑。
2. **檢查日誌**：查看控制台輸出的異常堆棧，定位錯誤發生位置。
3. **分析根本原因**：不只是修復錯誤，要理解「為什麼」會發生（技術層面）。
4. **解決問題**：實作修復方案，參考 `SPEC_Error_Handling.md` 的錯誤處理策略。
5. **更新 `error_log.md`**：記錄以下內容：
   - **錯誤訊息**：簡述或複製關鍵錯誤 log
   - **根本原因 (Root Cause)**：解釋為什麼會發生（技術層面）
   - **解決方案**：你做了什麼修正
   - **學習點**：這個錯誤帶來的知識或經驗
6. **實作降級**：確保即使某個 Agent 失敗，整體報告仍能生成（優雅降級）。

## 📝 Git Commit 規範 (繁體中文)

### Commit Message 格式

```
<類型>: <簡短描述>

[可選的詳細說明]
```

### 類型 (Type) 定義

| 類型 | 說明 | 範例 |
|------|------|------|
| **新增** | 新開發功能、Agent 或採集器 | `新增: 實作 Polymarket 數據採集器` |
| **修正** | Bug 修復、邏輯錯誤修補 | `修正: 處理美債殖利率曲線倒掛計算錯誤` |
| **文件** | 文件更新、README、Spec 調整 | `文件: 更新主編 Agent 的設計規格書` |
| **重構** | 代碼優化、架構調整、不改變功能 | `重構: 提取 Agent 共用的 Prompt 渲染邏輯` |
| **維護** | 更新依賴、環境配置、雜項調整 | `維護: 更新 OpenAI SDK 版本` |
| **優化** | 性能提升、Token 消耗減少 | `優化: 實作數據分段處理以節省 Context` |

## 🛡️ 錯誤處理與安全原則

### API 調用準則

- **重試機制**：必須實作至少 3 次的指數退避重試 (Exponential Backoff)。
- **超時設定**：所有外部 API 請求必須設置 timeout (預設 10s)。
- **資料驗證**：嚴禁直接使用 API 回傳的 JSON 進行運算，必須經過 Pydantic 解析。

### 安全性原則

- **金鑰保護**：絕對禁止在代碼中寫死 API Key。`.env` 必須加入 `.gitignore`。
- **敏感資訊**：日誌中嚴禁輸出包含 `apiKey`, `token` 或用戶個人持倉細節的全量 Response。

## 🧪 測試原則

### 測試腳本位置

所有的單體測試應放在 `test_scripts/` 目錄：

- `test_polymarket.py`: 驗證 API 解析邏輯。
- `test_prompts.py`: 測試各個 Agent 的 Prompt 回傳是否符合 JSON 格式。

### 測試範本

```python
async def test_agent_output():
    """驗證 Agent 輸出是否符合 Pydantic 模型"""
    agent = FedAgent()
    result = await agent.analyze(mock_data)
    assert isinstance(result, AnalysisSchema)
    print("✅ 分析模型驗證通過")
```

## 🤖 AI 協作提示

### 開始新任務時
1. **閱讀 `TODO.md`**：了解當前優先級和待辦事項
2. **查看相關規格文件**：根據任務類型閱讀對應的 `Spec_Agent_*.md` 或 `SPEC_*.md`
3. **檢查 `error_log.md`**：避免重複已知問題，學習過往經驗

### 完成任務後
1. **更新 `TODO.md`**：標記任務完成狀態
2. **如果遇到錯誤**：必須更新 `error_log.md`，記錄錯誤、根本原因、解決方案和學習點
3. **撰寫清晰的 commit message**：遵循 Git Commit 規範

### 解決問題時
- 優先查看 `error_log.md` 是否有類似案例
- 參考 `SPEC_Error_Handling.md` 的錯誤處理策略
- 記錄解決過程到 `error_log.md`，幫助未來的開發者

## 📌 環境工具速查

### uv 管理 (推薦)

```bash
uv sync                 # 同步專案依賴
uv add httpx pydantic   # 新增套件
uv run main.py          # 執行主程式
```

### Windows 環境注意事項

若在 Windows 本地執行，請確保環境變數設定 `PYTHONUTF8=1`。

執行指令：
```powershell
$env:PYTHONUTF8=1; uv run python main.py
```

---

**📅 文件版本**：v1.1  
**🤖 開發代理**：Cursor Agent (Macro Intelligence)
