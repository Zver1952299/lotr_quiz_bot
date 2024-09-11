import asyncio
import logging
from aiogram import Bot
from settings import API_TOKEN
from dispathers import create_table, dp

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)


async def main():

    await create_table()

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
