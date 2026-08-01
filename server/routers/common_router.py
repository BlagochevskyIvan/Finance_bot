from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram import Update

from config.envcfg import BOT_ENABLED, TELEGRAM_SECRET, WEBHOOK_PATH
from config.logger import logger

router = APIRouter()


@router.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"service": "base-telegram-bot", "status": "ok"})


@router.get("/healthz")
async def health() -> PlainTextResponse:
    return PlainTextResponse("ok")


@router.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> Response:
    if not BOT_ENABLED or not hasattr(request.app.state, "bot_app"):
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    if TELEGRAM_SECRET:
        header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header_token != TELEGRAM_SECRET:
            logger.warning("Rejected Telegram webhook with an invalid secret")
            return Response(status_code=status.HTTP_403_FORBIDDEN)

    try:
        payload = await request.json()
        update = Update.de_json(payload, request.app.state.bot_app.bot)
    except (TypeError, ValueError):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    await request.app.state.bot_app.update_queue.put(update)
    return Response(status_code=status.HTTP_200_OK)
