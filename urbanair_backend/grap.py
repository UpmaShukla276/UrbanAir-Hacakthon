"""
GRAP (Graded Response Action Plan) rules engine
=================================================
Static CAQM stage thresholds + summarized mandated actions.
Source: CAQM revised GRAP schedule (21.11.2025), caqm.nic.in
"""

GRAP_STAGES = [
    {
        "stage": 1, "label": "Stage I", "category": "Poor",
        "aqi_min": 201, "aqi_max": 300, "color": "#FF7A00",
        "actions": [
            "Strict action on garbage/waste burning",
            "Mechanized road sweeping & water sprinkling on major roads",
            "Enforce dust-control norms at all C&D sites",
            "Strict PUC enforcement; diesel gensets only for essential services",
        ],
    },
    {
        "stage": 2, "label": "Stage II", "category": "Very Poor",
        "aqi_min": 301, "aqi_max": 400, "color": "#D9534F",
        "actions": [
            "Intensify public transport frequency; raise parking fees",
            "Ensure uninterrupted power supply so diesel gensets aren't needed",
            "Deploy anti-smog guns / extra water sprinkling at hotspots",
            "Stricter, more frequent inspection of industrial units",
        ],
    },
    {
        "stage": 3, "label": "Stage III", "category": "Severe",
        "aqi_min": 401, "aqi_max": 450, "color": "#7B1F1F",
        "actions": [
            "Halt all construction/demolition (except essential/exempted)",
            "Ban entry of non-essential diesel MGVs/HGVs into Delhi",
            "State discretion: restrict BS-III petrol / BS-IV diesel 4-wheelers",
            "State discretion: shift schools to hybrid/online",
        ],
    },
    {
        "stage": 4, "label": "Stage IV", "category": "Severe+",
        "aqi_min": 451, "aqi_max": 10000, "color": "#4A0E0E",
        "actions": [
            "Stop entry of trucks into Delhi (except essential goods)",
            "Halt all construction/demolition, including public infra",
            "State discretion: odd-even vehicle rationing",
            "State discretion: 50% WFH for govt/private staff, close colleges",
        ],
    },
]


def stage_for_aqi(aqi):
    if aqi is None:
        return None
    for s in GRAP_STAGES:
        if s["aqi_min"] <= aqi <= s["aqi_max"]:
            return s
    return None


def zone_grap_status(point, current_aqi, forecast_24h_aqi, forecast_is_warming_up):
    current_stage = stage_for_aqi(current_aqi)
    forecast_stage = stage_for_aqi(forecast_24h_aqi)

    current_num = current_stage["stage"] if current_stage else 0
    forecast_num = forecast_stage["stage"] if forecast_stage else 0

    recommended_stage = forecast_stage if forecast_num > current_num else current_stage
    escalation = forecast_num > current_num

    return {
        "point": point,
        "current_aqi": current_aqi,
        "forecast_aqi_24h": forecast_24h_aqi,
        "current_stage": current_stage,
        "recommended_stage": recommended_stage,
        "escalation_warning": escalation,
        "forecast_is_warming_up": forecast_is_warming_up,
    }