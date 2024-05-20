from app.database.models import async_session
from app.database.models import User
from sqlalchemy import select
from sqlalchemy import BigInteger, String

import json


async def set_user(tg_id: BigInteger, number: String) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, number=number, history="[]", balance=1))
            await session.commit()

async def have_user(tg_id: BigInteger) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            return True
        else:
            return False
        

async def get_balance(tg_id: BigInteger) -> int:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            return user.balance
        
async def get_number(tg_id: BigInteger) -> str:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            return user.number
        
async def get_history(tg_id: BigInteger) -> list:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            if user.history == []:
                return []
            else:
                history = json.loads(user.history)
                return history


async def update_history(tg_id: BigInteger, history: list) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            user.history = json.dumps(history, ensure_ascii=False)
            await session.commit()

async def update_balance_dialog(tg_id: BigInteger) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            user.balance = user.balance - 1
            await session.commit()

async def update_balance_pay(tg_id: BigInteger, amount: int) -> None:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user:
            user.balance = user.balance + amount
            await session.commit()