"""虚拟教师 API - 讯飞超拟人语音合成 WebSocket 配置接口。

提供虚拟教师 TTS 配置信息，供前端 WebSocket 直连讯飞超拟人语音合成服务使用。
前端通过 HMAC-SHA256 鉴权直接建立 WebSocket 连接，无需后端代理。
"""
import os

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/virtual-teacher", tags=["virtual-teacher"])

# 讯飞超拟人语音合成 WebSocket 服务地址
XUNFEI_TTS_WS_URL = "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6"


@router.get("/config")
async def get_virtual_teacher_config():
    """返回虚拟教师 TTS 配置（前端用于 WebSocket 鉴权连接）"""
    app_id = os.getenv("XUNFEI_DIGITAL_HUMAN_APPID", "")
    api_key = os.getenv("XUNFEI_DIGITAL_HUMAN_KEY", "")
    api_secret = os.getenv("XUNFEI_DIGITAL_HUMAN_SECRET", "")
    vcn = os.getenv("XUNFEI_DIGITAL_HUMAN_VCN", "x6_lingxiaoxuan_flow")

    return {
        "appId": app_id,
        "apiKey": api_key,
        "apiSecret": api_secret,
        "vcn": vcn,
        "wsUrl": XUNFEI_TTS_WS_URL,
        "enabled": bool(app_id and api_key and api_secret),
        "mode": "websocket-tts",
        "description": "讯飞超拟人语音合成 WebSocket API，前端直连",
    }


@router.get("/voices")
async def get_available_voices():
    """返回可用的发音人列表"""
    current_vcn = os.getenv("XUNFEI_DIGITAL_HUMAN_VCN", "x6_lingxiaoxuan_flow")

    voices = [
        {
            "vcn": "x6_lingxiaoxuan_flow",
            "name": "聆小璇",
            "gender": "女",
            "description": "温柔知性，适合教学交互",
            "isDefault": current_vcn == "x6_lingxiaoxuan_flow",
        },
        {
            "vcn": "x6_lingfeiyi_flow",
            "name": "聆飞逸",
            "gender": "男",
            "description": "沉稳自然，适合讲解",
            "isDefault": current_vcn == "x6_lingfeiyi_flow",
        },
        {
            "vcn": "x6_lingxiaoyue_flow",
            "name": "聆小玥",
            "gender": "女",
            "description": "亲切活泼，适合互动问答",
            "isDefault": current_vcn == "x6_lingxiaoyue_flow",
        },
        {
            "vcn": "x6_lingyuzhao_flow",
            "name": "聆玉昭",
            "gender": "女",
            "description": "端庄优雅，适合正式讲解",
            "isDefault": current_vcn == "x6_lingyuzhao_flow",
        },
        {
            "vcn": "x6_lingyuyan_flow",
            "name": "聆玉言",
            "gender": "女",
            "description": "清晰流畅，适合课程朗读",
            "isDefault": current_vcn == "x6_lingyuyan_flow",
        },
    ]

    return {"voices": voices, "currentVcn": current_vcn}
