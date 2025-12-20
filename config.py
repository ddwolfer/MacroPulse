"""
配置管理模組

使用 Pydantic Settings 管理所有環境變數和配置。
參考文件：SPEC_Configuration.md
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List, Dict
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """應用程式配置"""
    
    # ============================================
    # LLM 配置
    # ============================================
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API Key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key（備選）")
    llm_provider: str = Field(
        "gemini", 
        description="LLM 提供商: 'gemini' 或 'openai'"
    )
    llm_model: str = Field(
        "gemini-flash-latest", 
        description="LLM 模型名稱"
    )
    llm_temperature: float = Field(
        0.3, 
        description="LLM 溫度設定 (0.0-1.0)", 
        ge=0.0, 
        le=1.0
    )
    editor_temperature: float = Field(
        0.5, 
        description="Editor Agent 溫度 (可稍高，需要創造性)", 
        ge=0.0, 
        le=1.0
    )
    max_tokens: int = Field(
        4000, 
        description="最大 Token 數", 
        gt=0
    )
    
    # ============================================
    # API Keys
    # ============================================
    fred_api_key: Optional[str] = Field(
        None, 
        description="FRED API Key (必需)"
    )
    polymarket_api_key: Optional[str] = Field(
        None, 
        description="Polymarket API Key (可選，目前不需要)"
    )
    
    # ============================================
    # 用戶配置
    # ============================================
    user_portfolio: Optional[str] = Field(
        None, 
        description="用戶持倉 (JSON 格式)"
    )
    
    # ============================================
    # 系統配置
    # ============================================
    log_level: str = Field(
        "INFO", 
        description="日誌級別: DEBUG, INFO, WARNING, ERROR"
    )
    data_cache_dir: Path = Field(
        Path("./data_cache"), 
        description="數據緩存目錄"
    )
    output_dir: Path = Field(
        Path("./outputs"), 
        description="輸出目錄"
    )
    request_timeout: float = Field(
        10.0, 
        description="請求超時時間（秒）", 
        gt=0.0
    )
    max_retries: int = Field(
        3, 
        description="API 重試次數", 
        ge=1
    )
    retry_initial_delay: float = Field(
        1.0, 
        description="API 重試初始延遲（秒）", 
        gt=0.0
    )
    retry_backoff_factor: float = Field(
        2.0, 
        description="API 重試退避因子", 
        gt=1.0
    )
    
    # ============================================
    # 緩存配置
    # ============================================
    fred_cache_ttl: int = Field(
        24, 
        description="FRED 數據緩存 TTL（小時）", 
        gt=0
    )
    polymarket_cache_ttl: int = Field(
        1, 
        description="Polymarket 數據緩存 TTL（小時）", 
        gt=0
    )
    yfinance_cache_ttl: int = Field(
        15, 
        description="yfinance 數據緩存 TTL（分鐘）", 
        gt=0
    )
    
    # ============================================
    # 數據過濾配置
    # ============================================
    polymarket_min_volume: float = Field(
        100000.0, 
        description="Polymarket 最小交易量門檻（USD）", 
        ge=0.0
    )
    correlation_days: int = Field(
        7, 
        description="相關係數計算的歷史天數", 
        ge=1, 
        le=30
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """驗證 LLM 提供商"""
        if v not in ["openai", "gemini"]:
            raise ValueError("LLM_PROVIDER 必須是 'openai' 或 'gemini'")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """驗證日誌級別"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL 必須是 {', '.join(valid_levels)} 之一")
        return v_upper
    
    def get_user_portfolio_list(self) -> List[Dict]:
        """
        解析用戶持倉 JSON 字串
        
        Returns:
            List[Dict]: 持倉列表，每個元素包含 symbol 和 quantity
            
        Example:
            [
                {"symbol": "BTC-USD", "quantity": 1.5},
                {"symbol": "ETH-USD", "quantity": 10.0}
            ]
        """
        if not self.user_portfolio:
            return []
        
        try:
            portfolio = json.loads(self.user_portfolio)
            if not isinstance(portfolio, list):
                logger.warning("USER_PORTFOLIO 格式錯誤：必須是 JSON 陣列")
                return []
            return portfolio
        except json.JSONDecodeError as e:
            logger.warning(f"無法解析 USER_PORTFOLIO：{str(e)}")
            return []
    
    def validate_required_keys(self) -> None:
        """
        驗證必要的 API Key 是否存在
        
        Raises:
            ValueError: 缺少必要的 API Key
        """
        errors = []
        
        # 驗證 LLM API Key
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            errors.append("缺少 GEMINI_API_KEY（當 LLM_PROVIDER=gemini 時）")
        elif self.llm_provider == "openai" and not self.openai_api_key:
            errors.append("缺少 OPENAI_API_KEY（當 LLM_PROVIDER=openai 時）")
        
        # 驗證 FRED API Key（必需）
        if not self.fred_api_key:
            errors.append("缺少 FRED_API_KEY（必需）")
        
        if errors:
            error_msg = "配置驗證失敗：\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
    
    def ensure_directories(self) -> None:
        """確保所有必要的目錄存在"""
        self.data_cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 建立子目錄
        (self.data_cache_dir / "fred").mkdir(parents=True, exist_ok=True)
        (self.data_cache_dir / "polymarket").mkdir(parents=True, exist_ok=True)
        (self.data_cache_dir / "yfinance").mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"數據緩存目錄：{self.data_cache_dir}")
        logger.debug(f"輸出目錄：{self.output_dir}")


# 全域設定實例
settings = Settings()


def validate_config() -> None:
    """
    驗證配置完整性（用於啟動時檢查）
    
    Raises:
        ValueError: 配置不完整
    """
    try:
        settings.validate_required_keys()
        settings.ensure_directories()
        logger.info("✅ 配置驗證通過")
    except ValueError as e:
        logger.error(str(e))
        raise

