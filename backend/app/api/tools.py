"""API endpoints for Tool and Data Connectors."""

import logging
import urllib.parse
import httpx
from fastapi import APIRouter
from fastapi.responses import Response

logger = logging.getLogger("agrimind.tools.tts")
from backend.app.schemas.tools import ToolResult
from backend.app.tools.weather import default_weather_connector, WeatherQueryInput
from backend.app.tools.knowledge import default_knowledge_tool, KnowledgeQueryInput
from backend.app.tools.structured_data import default_structured_tool, DataQueryInput
from backend.app.tools.web_search import default_web_search_connector, WebSearchQueryInput

router = APIRouter(prefix="/v1/tools", tags=["Tool and Data Connectors"])


@router.post("/weather", response_model=ToolResult)
def fetch_weather_telemetry(query: WeatherQueryInput):
    """
    Fetch live or historical meteorological telemetry via Open-Meteo API.
    Calculates thermal stress indices and whitefly vector proliferation risk.
    """
    return default_weather_connector.fetch_weather(query)


@router.post("/knowledge", response_model=ToolResult)
def search_agricultural_guidance(query: KnowledgeQueryInput):
    """
    Execute semantic retrieval against indexed ICAR/university extension bulletins using FAISS.
    """
    return default_knowledge_tool.retrieve(query)


@router.post("/structured", response_model=ToolResult)
def query_parcel_and_soil_data(query: DataQueryInput):
    """
    Query and filter tabular soil testing and parcel management records using Pandas.
    """
    return default_structured_tool.query(query)


@router.post("/web-search", response_model=ToolResult)
def search_web_information(query: WebSearchQueryInput):
    """
    Execute live web query across external knowledge sources with structured citations.
    """
    return default_web_search_connector.search(query)


@router.get("/tts")
async def generate_speech_audio(text: str, lang: str = "te"):
    """
    Stream high-fidelity MP3 speech audio for any requested language (Telugu, Tamil, Hindi, Kannada, Malayalam, English).
    Guarantees seamless voice output across all devices and OS without requiring local voice pack installations.
    """
    clean_text = text.strip()[:300]
    if not clean_text:
        return Response(content=b"", media_type="audio/mpeg")

    encoded_text = urllib.parse.quote(clean_text)
    lang_code = lang.lower().split("-")[0]
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang_code}&q={encoded_text}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return Response(
                    content=resp.content,
                    media_type="audio/mpeg",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
    except Exception as e:
        logger.warning(f"TTS audio streaming failed: {e}")

    return Response(status_code=500, content=b"Could not stream speech audio", media_type="text/plain")
