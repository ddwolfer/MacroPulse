"""
基礎 Agent 類別

提供所有專業 Agent 的共同介面和 LLM 調用邏輯。
參考文件：SPEC_Prompt_Templates.md, SPEC_Error_Handling.md
"""

import asyncio
import logging
import json
from typing import Optional, Any, Type, TypeVar, Dict
from abc import ABC, abstractmethod

try:
    # 優先使用新版 API
    from google import genai
    USE_NEW_GENAI = True
except ImportError:
    # 回退到舊版 API
    import google.generativeai as genai
    USE_NEW_GENAI = False

from pydantic import BaseModel, ValidationError

from config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class AgentExecutionError(Exception):
    """Agent 執行錯誤"""
    
    def __init__(
        self, 
        agent_name: str, 
        error_type: str, 
        error_message: str, 
        can_continue: bool = True
    ):
        self.agent_name = agent_name
        self.error_type = error_type
        self.error_message = error_message
        self.can_continue = can_continue
        super().__init__(f"{agent_name}: {error_message}")


class BaseAgent(ABC):
    """
    基礎 Agent 抽象類別
    
    提供：
    - LLM 調用邏輯（支援 Gemini 和 OpenAI）
    - Prompt 渲染
    - 錯誤處理和重試
    - 輸出驗證
    """
    
    def __init__(
        self,
        name: str,
        temperature: Optional[float] = None,
        max_retries: int = 3
    ):
        """
        初始化 Agent
        
        Args:
            name: Agent 名稱
            temperature: LLM 溫度（None 使用全域設定）
            max_retries: 最大重試次數
        """
        self.name = name
        self.temperature = temperature or settings.llm_temperature
        self.max_retries = max_retries
        self.llm_provider = settings.llm_provider
        
        # 初始化 LLM 客戶端
        if self.llm_provider == "gemini":
            if USE_NEW_GENAI:
                # 新版 API
                self.client = genai.Client(api_key=settings.gemini_api_key)
            else:
                # 舊版 API
                genai.configure(api_key=settings.gemini_api_key)
                self.model = genai.GenerativeModel(settings.llm_model)
        elif self.llm_provider == "openai":
            # 保留給未來擴展
            raise NotImplementedError("OpenAI 支援尚未實作")
        
        logger.debug(f"初始化 {self.name} Agent（LLM: {self.llm_provider}, 新API: {USE_NEW_GENAI}）")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        獲取 System Prompt
        
        子類別必須實作此方法。
        
        Returns:
            str: System Prompt 內容
        """
        pass
    
    @abstractmethod
    def format_user_prompt(self, data: Any) -> str:
        """
        格式化 User Prompt
        
        子類別必須實作此方法，根據輸入數據生成 Prompt。
        
        Args:
            data: 輸入數據
            
        Returns:
            str: 格式化後的 User Prompt
        """
        pass
    
    @abstractmethod
    def get_output_model(self) -> Type[BaseModel]:
        """
        獲取輸出模型類別
        
        子類別必須實作此方法，返回對應的 Pydantic 模型。
        
        Returns:
            Type[BaseModel]: 輸出模型類別
        """
        pass
    
    async def analyze(self, data: Any) -> Optional[BaseModel]:
        """
        執行分析（主要入口）
        
        Args:
            data: 輸入數據
            
        Returns:
            Optional[BaseModel]: 分析結果，失敗則返回 None
        """
        try:
            logger.info(f"{self.name} 開始分析...")
            
            # 格式化 Prompt
            user_prompt = self.format_user_prompt(data)
            
            # 調用 LLM
            result = await self._call_llm_with_retry(user_prompt)
            
            if not result:
                logger.warning(f"{self.name} LLM 調用失敗")
                return None
            
            # 解析和驗證輸出
            output_model = self.get_output_model()
            validated_result = self._validate_output(result, output_model)
            
            if validated_result:
                logger.info(f"✅ {self.name} 分析完成")
            else:
                logger.warning(f"{self.name} 輸出驗證失敗")
            
            return validated_result
            
        except Exception as e:
            error = self._handle_error(e)
            if not error.can_continue:
                raise
            return None
    
    async def _call_llm_with_retry(self, user_prompt: str) -> Optional[str]:
        """
        帶重試機制的 LLM 調用
        
        Args:
            user_prompt: 用戶 Prompt
            
        Returns:
            Optional[str]: LLM 輸出，失敗則返回 None
        """
        for attempt in range(self.max_retries):
            try:
                if self.llm_provider == "gemini":
                    result = await self._call_gemini(user_prompt)
                else:
                    raise NotImplementedError(f"不支援的 LLM 提供商: {self.llm_provider}")
                
                return result
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"{self.name} LLM 調用重試 {self.max_retries} 次後仍然失敗: {str(e)}"
                    )
                    return None
                
                delay = 2 ** attempt  # 指數退避: 1s, 2s, 4s
                logger.warning(
                    f"{self.name} LLM 調用失敗（嘗試 {attempt + 1}/{self.max_retries}），"
                    f"等待 {delay} 秒後重試: {str(e)}"
                )
                await asyncio.sleep(delay)
        
        return None
    
    async def _call_gemini(self, user_prompt: str) -> str:
        """
        調用 Gemini API
        
        Args:
            user_prompt: 用戶 Prompt
            
        Returns:
            str: LLM 輸出
        """
        # 組合完整 Prompt
        system_prompt = self.get_system_prompt()
        full_prompt = f"""{system_prompt}

---

{user_prompt}

---

請以 JSON 格式輸出分析結果。"""
        
        logger.debug(f"{self.name} 調用 Gemini API...")
        
        # 非同步調用（使用 asyncio.to_thread 包裝同步 API）
        def _sync_generate():
            if USE_NEW_GENAI:
                # 新版 API
                response = self.client.models.generate_content(
                    model=settings.llm_model,
                    contents=full_prompt,
                    config={
                        "temperature": self.temperature,
                        "max_output_tokens": settings.max_tokens,
                        "response_mime_type": "application/json"
                    }
                )
                return response.text
            else:
                # 舊版 API
                generation_config = {
                    "temperature": self.temperature,
                    "max_output_tokens": settings.max_tokens,
                    "response_mime_type": "application/json"
                }
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                return response.text
        
        result = await asyncio.to_thread(_sync_generate)
        
        logger.debug(f"{self.name} 收到 LLM 回應（{len(result)} 字元）")
        return result
    
    def _validate_output(
        self, 
        llm_output: str, 
        model_class: Type[T]
    ) -> Optional[T]:
        """
        驗證和解析 LLM 輸出
        
        Args:
            llm_output: LLM 原始輸出
            model_class: Pydantic 模型類別
            
        Returns:
            Optional[T]: 驗證後的模型實例，失敗則返回 None
        """
        try:
            # 嘗試解析 JSON
            data = json.loads(llm_output)
            
            # 使用 Pydantic 驗證
            validated = model_class(**data)
            
            logger.debug(f"{self.name} 輸出驗證通過")
            return validated
            
        except json.JSONDecodeError as e:
            logger.error(f"{self.name} JSON 解析失敗: {str(e)}")
            logger.debug(f"原始輸出: {llm_output[:200]}...")
            
            # 嘗試修復常見的 JSON 錯誤
            fixed_output = self._try_fix_json(llm_output)
            if fixed_output:
                try:
                    data = json.loads(fixed_output)
                    validated = model_class(**data)
                    logger.info(f"{self.name} JSON 修復成功")
                    return validated
                except Exception:
                    pass
            
            return None
            
        except ValidationError as e:
            logger.error(f"{self.name} Pydantic 驗證失敗: {str(e)}")
            logger.debug(f"原始數據: {llm_output[:200]}...")
            return None
            
        except Exception as e:
            logger.error(f"{self.name} 輸出驗證發生未預期錯誤: {str(e)}")
            return None
    
    def _try_fix_json(self, text: str) -> Optional[str]:
        """
        嘗試修復常見的 JSON 錯誤
        
        Args:
            text: 原始文本
            
        Returns:
            Optional[str]: 修復後的 JSON，失敗則返回 None
        """
        try:
            # 移除 Markdown 代碼塊標記
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            
            # 嘗試找到第一個 { 和最後一個 }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]
            
            # 驗證是否為有效 JSON
            json.loads(text)
            return text
            
        except Exception:
            return None
    
    def _handle_error(self, error: Exception) -> AgentExecutionError:
        """
        處理 Agent 錯誤
        
        Args:
            error: 原始錯誤
            
        Returns:
            AgentExecutionError: 包裝後的錯誤
        """
        error_type = type(error).__name__
        can_continue = not isinstance(error, (KeyboardInterrupt, SystemExit))
        
        logger.error(f"{self.name} 執行失敗: {error_type} - {str(error)}")
        
        return AgentExecutionError(
            agent_name=self.name,
            error_type=error_type,
            error_message=str(error),
            can_continue=can_continue
        )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        獲取 Agent 資訊
        
        Returns:
            Dict[str, Any]: Agent 資訊
        """
        return {
            "name": self.name,
            "llm_provider": self.llm_provider,
            "temperature": self.temperature,
            "max_retries": self.max_retries
        }

