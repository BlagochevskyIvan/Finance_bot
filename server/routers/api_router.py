from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import User
from server.auth.telegram import TelegramUser
from server.dependency.auth import get_current_telegram_user
from server.schemas.user import UserResponse

router = APIRouter()


@router.get("/health")
async def api_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    telegram_user: TelegramUser = Depends(get_current_telegram_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_user.id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_user.id)
        session.add(user)

    user.username = telegram_user.username
    user.first_name = telegram_user.first_name
    user.last_name = telegram_user.last_name
    await session.commit()
    await session.refresh(user)
    return user
