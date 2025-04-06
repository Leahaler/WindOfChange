'''
Set-ExecutionPolicy RemoteSigned -Scope Process
.venv scriptsactivate
python run.py
'''

import asyncio 
import logging

from aiogram import Bot, Dispatcher
from app.handlers import router
from app.locations import start_auto_spawn_items  # Импортируем функцию запуска

from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(router)
    start_auto_spawn_items()  # Запускаем фоновую задачу спавна ресурсов
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)  # Устанавливаем DEBUG для отладки
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')