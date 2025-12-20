# 錯誤日誌 (Error Log) & 學習筆記

這份文件記錄了專案開發過程中的技術障礙、錯誤訊息、根本原因分析 (Root Cause Analysis) 以及解決方案。目標是累積知識庫，不僅是解決問題，更要理解「為什麼」會發生以及「為什麼」這樣修有效。

## 📝 記錄格式

每次遇到錯誤並解決後，請按照以下格式記錄：

```markdown
### [錯誤編號] 簡短錯誤描述

**發生時間**：YYYY-MM-DD  
**發生位置**：檔案/模組名稱  
**錯誤類型**：API 錯誤 / LLM 錯誤 / 數據驗證錯誤 / 其他

#### 1. 錯誤訊息
簡述或複製關鍵錯誤 log

#### 2. 根本原因 (Root Cause)
解釋為什麼會發生（技術層面）

#### 3. 解決方案
你做了什麼修正

#### 4. 學習點
這個錯誤帶來的知識或經驗
```

---

## 📚 錯誤記錄

### [ERROR-001] Windows 控制台 UnicodeEncodeError - Emoji 字符編碼問題

**發生時間**：2024-12-20  
**發生位置**：`src/utils/logger.py`  
**錯誤類型**：系統編碼錯誤

#### 1. 錯誤訊息

```python
UnicodeEncodeError: 'cp950' codec can't encode character '\u2705' in position 51: illegal multibyte sequence
```

在 Windows 環境執行 `main.py` 時，日誌輸出包含 emoji 字符（如 ✅、📄）時會發生編碼錯誤。

#### 2. 根本原因 (Root Cause)

Windows PowerShell 預設使用 `cp950` (Big5) 編碼，而 Python 的 `logging.StreamHandler(sys.stdout)` 會繼承系統的預設編碼。當日誌訊息包含 UTF-8 特殊字符（emoji）時，無法用 `cp950` 編碼，導致異常。

**技術細節**：
- Windows 控制台預設編碼：`cp950` 或 `cp1252`
- Python 3.10+ 預設使用 UTF-8 字串
- `logging.StreamHandler` 預設使用 `sys.stdout.encoding`
- Emoji 字符需要 UTF-8 編碼

#### 3. 解決方案

修改 `src/utils/logger.py` 的 `setup_logger` 函數，針對 Windows 環境使用 UTF-8 編碼的 StreamHandler：

```python
if sys.platform == "win32":
    import io
    # 使用 UTF-8 編碼的 stdout，並設定 errors='replace' 避免編碼失敗
    console_handler = logging.StreamHandler(
        io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    )
else:
    console_handler = logging.StreamHandler(sys.stdout)
```

**關鍵點**：
- 使用 `sys.stdout.buffer` 取得原始二進制串流
- 使用 `io.TextIOWrapper` 包裝並指定 `encoding='utf-8'`
- 設定 `errors='replace'` 讓無法編碼的字符被替換而不是拋出異常

#### 4. 學習點

1. **跨平台編碼處理**：Python 程式需要考慮不同作業系統的預設編碼差異
2. **Windows 特殊處理**：Windows 環境的編碼問題比 Linux/macOS 更複雜
3. **日誌系統設計**：應該在 logger 設定階段就處理好編碼問題，而不是在使用時才發現
4. **容錯設計**：使用 `errors='replace'` 而非 `errors='strict'` 可以避免程式因編碼問題而崩潰

**最佳實踐**：
- 在 Windows 環境開發時，在程式入口處設定 `os.environ["PYTHONUTF8"] = "1"`（已在 `main.py` 實作）
- Logger 設定時考慮平台差異
- 日誌訊息盡量使用純文字，emoji 等特殊字符應該是可選的

---

### [ERROR-002] .env.example 繁體中文註解在 PowerShell 顯示亂碼

**發生時間**：2024-12-20  
**發生位置**：`.env.example`  
**錯誤類型**：終端機顯示編碼問題

#### 1. 錯誤訊息

在 Windows PowerShell 使用 `Get-Content` 讀取 `.env.example` 時，繁體中文註解顯示為亂碼。

#### 2. 根本原因 (Root Cause)

這是 Windows PowerShell 終端機的顯示問題，而非檔案編碼問題：

**技術細節**：
- `.env.example` 檔案本身是正確的 UTF-8 編碼（使用 Python 驗證通過）
- Windows PowerShell 預設使用 cp950 (Big5) 編碼顯示
- `Get-Content -Encoding UTF8` 仍然會在顯示時轉換為終端機編碼
- 這只影響終端機顯示，不影響程式讀取

#### 3. 解決方案

**檔案建立方式**：
使用 Python 建立檔案確保正確的 UTF-8 編碼：

```python
with open('.env.example', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
```

**驗證方法**：
使用 Python 驗證檔案內容（而非依賴 PowerShell 顯示）：

```python
with open('.env.example', 'r', encoding='utf-8') as f:
    content = f.read()
    assert 'OpenAI API' in content  # 驗證關鍵詞
```

**結論**：檔案本身沒有問題，只是 PowerShell 顯示的視覺問題。

#### 4. 學習點

1. **檔案編碼 vs 顯示編碼**：要區分檔案的實際編碼和終端機的顯示編碼
2. **驗證方法**：不要依賴終端機顯示來判斷檔案編碼是否正確，應該用程式驗證
3. **Windows 環境注意事項**：
   - PowerShell 的 `Get-Content` 即使指定 `-Encoding UTF8` 也會在顯示時轉換編碼
   - 應該使用 Python 等工具來處理 UTF-8 檔案
4. **最佳實踐**：
   - 使用 Python 建立包含繁體中文的配置檔案
   - 使用 Python 驗證檔案內容
   - 在程式中使用 `encoding='utf-8'` 參數

---

## 🔄 架構變更記錄

### [CHANGE-001] 切換主要 LLM 從 OpenAI 到 Google Gemini

**變更時間**：2024-12-20  
**變更範圍**：全專案配置  
**變更類型**：架構調整

#### 1. 變更原因

- 用戶擁有 Gemini 會員和 API Key，可享有更好的配額和速度
- 使用 `gemini-flash-latest` 避免模型版本過時問題（參考 Gemini Model 404 錯誤）
- Gemini Flash 性能優異且成本效益高，適合總經分析任務

#### 2. 主要變更

**預設 LLM 提供商**：
- 舊：OpenAI GPT-4
- 新：Google Gemini Flash

**預設模型**：
- 舊：`gpt-4`
- 新：`gemini-flash-latest`

**架構調整**：
- Gemini 為主要 LLM，OpenAI 為備選
- 使用 Latest Alias 確保長期可用性
- 保持雙 LLM 支援架構，可靈活切換

#### 3. 變更檔案清單

**Python 檔案**：
- ✅ `config.py` - 預設值和驗證邏輯（Gemini 優先）
- ✅ `requirements.txt` - 套件優先級調整（Gemini 為 Primary）

**Markdown 文件**：
- ✅ `README.md` - 技術棧說明更新
- ✅ `SPEC_Configuration.md` - 配置範例更新
- ✅ `.env.example` - 預設值更新
- ✅ `.env` - 測試配置更新

#### 4. 學習點

**使用 Latest Alias 的好處**：
- `gemini-flash-latest` 自動指向最新穩定版
- 避免手動追蹤版本號（如 `gemini-1.5-flash` 可能被棄用）
- Google/OpenAI 官方維護，確保長期可用
- 參考過往錯誤：Gemini Model 404（模型名稱過時導致 API 失敗）

**Gemini Flash 的優勢**：
- 速度快：適合需要快速響應的分析任務
- 成本低：比 GPT-4 更經濟
- 品質好：在經濟數據分析上表現優異
- 配額充足：有 Gemini 會員可享有更高的 API 限制

**最佳實踐**：
- 雲端 AI API 優先使用官方 Latest Alias
- 保持多 LLM 支援作為備援方案（OpenAI 作為 fallback）
- 在配置文件中明確註明主要/備選關係
- Temperature 設定：分析類任務使用 0.3，創意類任務（Editor）使用 0.5

#### 5. 後續行動

- ✅ 所有配置檔案已更新
- ✅ Phase 2 Gemini API 調用邏輯已完成
- ✅ `src/agents/base_agent.py` 已實作並支援雙 LLM 架構（新舊 Gemini API 兼容）
- ✅ 測試通過：BaseAgent 成功調用 Gemini Flash

---

### [ERROR-003] Google Gemini API 棄用警告 (FutureWarning)

**發生時間**：2024-12-20  
**發生位置**：`src/agents/base_agent.py`  
**錯誤類型**：API 版本過時警告

#### 1. 錯誤訊息

```
FutureWarning: All support for the `google.generativeai` package has ended. 
It will no longer be receiving updates or bug fixes. 
Please switch to the `google.genai` package as soon as possible.
```

執行測試時出現此警告，提示舊版 `google.generativeai` 已停止支援。

#### 2. 根本原因 (Root Cause)

Google 已推出新版 Gemini SDK (`google.genai`)，舊版 `google.generativeai` 已進入棄用階段：

**技術細節**：
- 舊版：`google-generativeai` 套件
- 新版：`google-genai` 套件
- API 結構差異：
  - 舊：`genai.GenerativeModel(model_name).generate_content()`
  - 新：`client.models.generate_content(model=..., contents=...)`

#### 3. 解決方案

實作新舊版本兼容的 BaseAgent：

```python
try:
    from google import genai
    USE_NEW_GENAI = True
except ImportError:
    import google.generativeai as genai
    USE_NEW_GENAI = False

# 初始化時
if USE_NEW_GENAI:
    self.client = genai.Client(api_key=settings.gemini_api_key)
else:
    genai.configure(api_key=settings.gemini_api_key)
    self.model = genai.GenerativeModel(settings.llm_model)

# 調用時
if USE_NEW_GENAI:
    response = self.client.models.generate_content(
        model=settings.llm_model,
        contents=full_prompt,
        config={...}
    )
else:
    response = self.model.generate_content(
        full_prompt,
        generation_config={...}
    )
```

**requirements.txt 更新**：
```
google-genai>=0.3.0          # 新版（優先）
google-generativeai>=0.3.0   # 舊版（回退）
```

#### 4. 學習點

1. **API 版本管理**：雲端 AI SDK 快速迭代，需要考慮版本兼容
2. **優雅降級**：優先使用新版 API，無法使用時回退到舊版
3. **依賴管理**：在 requirements.txt 中同時保留新舊版本，確保不同環境都能運行
4. **最佳實踐**：
   - 使用 try-except 處理 import，檢測可用的 API 版本
   - 在運行時動態選擇 API 版本
   - 記錄使用的 API 版本到日誌（方便除錯）
   - 優先使用官方推薦的新版 API
5. **架構靈活性**：BaseAgent 設計需要考慮不同 LLM 提供商和版本的差異

---

### [ERROR-004] PowerShell 不支援 && 運算符

**發生時間**：2024-12-20  
**發生位置**：測試腳本執行  
**錯誤類型**：Shell 語法錯誤

#### 1. 錯誤訊息

```
錯誤所在行:21 字元:21
+ cd d:\AI\MacroPulse && uv run python test_scripts/test_agents.py
+                     ~~
意外的 Token '&&'
```

在 Windows PowerShell 執行包含 `&&` 的命令時發生語法錯誤。

#### 2. 根本原因 (Root Cause)

**Shell 語法差異**：
- Bash/Zsh (Linux/macOS): 支援 `&&` 運算符（連接命令）
- PowerShell (Windows): 不支援 `&&`，使用 `;` 或換行分隔命令

**技術細節**：
- `&&` 在 Bash 中表示「前一個命令成功才執行下一個」
- PowerShell 使用不同的語法：
  - `;` - 依序執行
  - `&& (if)` - 需要用 `if ($?) { ... }` 結構

#### 3. 解決方案

**方案 1：使用分號**（PowerShell 語法）
```powershell
cd d:\AI\MacroPulse; uv run python test_scripts/test_agents.py
```

**方案 2：使用 Git Bash**（跨平台）
在 Windows 使用 Git Bash 可以支援 Bash 語法。

**方案 3：分別執行命令**
```powershell
cd d:\AI\MacroPulse
uv run python test_scripts/test_agents.py
```

#### 4. 學習點

1. **跨平台開發注意事項**：
   - 不同 Shell 的語法差異
   - Windows: PowerShell, CMD
   - Linux/macOS: Bash, Zsh
   
2. **最佳實踐**：
   - 文件中提供跨平台的命令範例
   - 使用工具（如 Make, Task）統一命令介面
   - 在 CI/CD 中明確指定 Shell 類型

3. **PowerShell 常用語法**：
   - 連接命令：使用 `;`
   - 條件執行：`if ($?) { ... }`
   - 管道：`|` (與 Bash 相同)
   - 邏輯或：`-or`
   - 邏輯且：`-and`

---

*持續更新中...*

---

**提示**：遇到錯誤時，先查看此文件是否有類似案例，避免重複踩坑。解決問題後，務必更新此文件幫助未來的開發者。
