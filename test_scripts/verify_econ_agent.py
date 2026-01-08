"""
快速驗證 Economic Agent

不需要 API 的基礎驗證
"""

import sys
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.econ_agent import EconAgent
from src.schema.models import FREDSeries, FREDObservation


def create_mock_fred_data() -> dict:
    """創建模擬的 FRED 經濟數據"""
    today = date.today()
    
    # CPI 數據（模擬過去 13 個月）
    cpi_observations = []
    base_cpi = 300.0
    for i in range(13):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        # 模擬 CPI 逐漸上升
        value = base_cpi + i * 0.3
        cpi_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    cpi_series = FREDSeries(
        series_id="CPIAUCSL",
        title="Consumer Price Index",
        observations=cpi_observations,
        units="Index 1982-1984=100",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # 失業率數據
    unrate_observations = []
    for i in range(6):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        # 模擬失業率在 3.7% 附近波動
        value = 3.7 + (i % 3) * 0.1
        unrate_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    unrate_series = FREDSeries(
        series_id="UNRATE",
        title="Unemployment Rate",
        observations=unrate_observations,
        units="Percent",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # 非農就業數據
    payems_observations = []
    base_nfp = 157000  # 千人
    for i in range(3):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        # 模擬每月增加約 200K
        value = base_nfp + i * 200
        payems_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    payems_series = FREDSeries(
        series_id="PAYEMS",
        title="Non-Farm Payroll",
        observations=payems_observations,
        units="Thousands of Persons",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # PCE 數據
    pcepi_observations = [
        FREDObservation(
            date=today,
            value=118.5,
            realtime_start=today,
            realtime_end=today
        )
    ]
    
    pcepi_series = FREDSeries(
        series_id="PCEPI",
        title="PCE Price Index",
        observations=pcepi_observations,
        units="Index 2012=100",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    return {
        "CPIAUCSL": cpi_series,
        "UNRATE": unrate_series,
        "PAYEMS": payems_series,
        "PCEPI": pcepi_series
    }


def test_econ_agent():
    """驗證 Economic Agent 基礎功能"""
    print("=" * 60)
    print("驗證 Economic Agent")
    print("=" * 60)
    
    # 測試 1：創建 Agent
    print("\n[測試 1] 創建 Economic Agent...")
    agent = EconAgent()
    print(f"  [OK] Agent 名稱: {agent.name}")
    print(f"  [OK] 溫度: {agent.temperature}")
    
    # 測試 2：System Prompt
    print("\n[測試 2] 獲取 System Prompt...")
    system_prompt = agent.get_system_prompt()
    print(f"  [OK] System Prompt 長度: {len(system_prompt)} 字元")
    assert "總體經濟學家" in system_prompt
    assert "軟著陸" in system_prompt
    assert "通膨" in system_prompt
    print("  [OK] System Prompt 內容正確")
    
    # 測試 3：User Prompt 生成
    print("\n[測試 3] 生成 User Prompt...")
    mock_data = create_mock_fred_data()
    test_data = {"fred_data": mock_data}
    
    user_prompt = agent.format_user_prompt(test_data)
    print(f"  [OK] User Prompt 長度: {len(user_prompt)} 字元")
    
    # 檢查 Prompt 包含正確內容
    assert "通膨數據" in user_prompt
    assert "就業數據" in user_prompt
    assert "CPI" in user_prompt
    assert "失業率" in user_prompt
    print("  [OK] User Prompt 包含所有必要區塊")
    
    # 顯示 Prompt 預覽
    print("\n  --- User Prompt 預覽 ---")
    preview_lines = user_prompt.split("\n")[:15]
    for line in preview_lines:
        print(f"  {line}")
    print("  ...")
    
    # 測試 4：輸出模型
    print("\n[測試 4] 獲取輸出模型...")
    output_model = agent.get_output_model()
    print(f"  [OK] 輸出模型: {output_model.__name__}")
    
    # 驗證模型欄位
    expected_fields = [
        "soft_landing_score",
        "inflation_trend",
        "employment_status",
        "key_indicators",
        "summary",
        "confidence"
    ]
    
    model_fields = list(output_model.model_fields.keys())
    for field in expected_fields:
        if field in model_fields:
            print(f"  [OK] 欄位存在: {field}")
        else:
            print(f"  [X] 欄位缺失: {field}")
            raise AssertionError(f"缺少欄位: {field}")
    
    # 測試 5：內部輔助函數
    print("\n[測試 5] 驗證輔助函數...")
    
    # 測試 _get_latest_value
    cpi_series = mock_data["CPIAUCSL"]
    latest_cpi = agent._get_latest_value(cpi_series)
    print(f"  [OK] _get_latest_value: {latest_cpi}")
    assert latest_cpi is not None
    
    # 測試 _get_cpi_analysis
    latest, prev, yoy = agent._get_cpi_analysis(cpi_series)
    print(f"  [OK] _get_cpi_analysis: latest={latest}, yoy={yoy}")
    
    # 測試 _get_nfp_analysis
    nfp_series = mock_data["PAYEMS"]
    nfp_latest, nfp_change = agent._get_nfp_analysis(nfp_series)
    print(f"  [OK] _get_nfp_analysis: latest={nfp_latest}, change={nfp_change}")
    
    # 總結
    print("\n" + "=" * 60)
    print(">>> 所有驗證通過!")
    print("=" * 60)
    print("\nEconomic Agent 準備就緒，可以開始分析。")
    print("\n提示：如要測試完整 LLM 分析，請執行:")
    print("  uv run python test_scripts/test_econ_agent.py")


if __name__ == "__main__":
    try:
        test_econ_agent()
    except Exception as e:
        print(f"\n[X] 驗證失敗: {str(e)}")
        import traceback
        traceback.print_exc()
