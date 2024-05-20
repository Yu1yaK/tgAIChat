from g4f.client import AsyncClient
from g4f import Provider

import app.database.requests as rq
from sqlalchemy import BigInteger

async def ask_gpt(question: str, tg_id: BigInteger) -> str:
    messages = await rq.get_history(tg_id)
    messages.append({"role": "user", "content": question})
    provider = Provider.DuckDuckGo

    client = AsyncClient()
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        provider=provider
    )

    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    await rq.update_history(tg_id, messages)
    return answer