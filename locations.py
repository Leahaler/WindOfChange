# app/locations.py
import json
import os
from datetime import datetime, timedelta
import random
import asyncio
import logging

logger = logging.getLogger(__name__)

locations = {}

def load_locations():
    global locations
    print("Starting load_locations()")
    try:
        file_path = 'locations.json'
        print(f"Checking for file: {os.path.abspath(file_path)}")
        with open(file_path, 'r', encoding='utf-8') as file:
            loaded_locations = json.load(file)
            print(f"Raw data from file: {loaded_locations}")
            for loc_id, loc_data in loaded_locations.items():
                loc_id = int(loc_id)
                if 'dropped_items' not in loc_data:
                    loc_data['dropped_items'] = []
                if 'last_herb_spawn' not in loc_data:
                    loc_data['last_herb_spawn'] = "2025-03-08T00:00:00"
                if 'last_mouse_spawn' not in loc_data:
                    loc_data['last_mouse_spawn'] = "2025-03-08T00:00:00"
                if 'herb_count' not in loc_data:
                    loc_data['herb_count'] = 8 if loc_id == 1 else 0
                if 'mouse_count' not in loc_data:
                    loc_data['mouse_count'] = 8 if loc_id == 1 else 0
                loc_data['dropped_items'] = [str(item_id) for item_id in loc_data['dropped_items']]
            locations.clear()
            locations.update({int(k): v for k, v in loaded_locations.items()})
            print(f"Loaded locations: {locations}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading locations.json: {e}")
        locations.update({
            1: {
                'name': 'Цветочная тропинка',
                'description': 'Окутанная нежным ароматом тропинка ведет сквозь зелень...',
                'adjacent': [2],
                'temperature': 18,
                'weather': 'солнечно',
                'dropped_items': [],
                'last_herb_spawn': "2025-03-08T00:00:00",
                'last_mouse_spawn': "2025-03-08T00:00:00",
                'herb_count': 8,
                'mouse_count': 8
            },
            2: {
                'name': 'Утиный пруд',
                'description': 'Тихий пруд окружен камышами...',
                'adjacent': [1],
                'temperature': 16,
                'weather': 'облачно',
                'dropped_items': [],
                'last_herb_spawn': "2025-03-08T00:00:00",
                'last_mouse_spawn': "2025-03-08T00:00:00",
                'herb_count': 0,
                'mouse_count': 0
            }
        })
        save_locations()
        print(f"Initialized default locations: {locations}")

def save_locations():
    with open('locations.json', 'w', encoding='utf-8') as file:
        json.dump(locations, file, ensure_ascii=False, indent=4)
    print(f"Saved locations: {locations}")

def spawn_items(location_id=1, spawn_type=None):
    """
    Обновляет количество трав (herb_count) и мышей (mouse_count) на локации 'Цветочная тропа' (ID 1),
    если прошло более 4 часов с последнего спавна.
    spawn_type: 'herbs', 'mice', или None (проверяет оба).
    """
    if location_id != 1:  # Спавн только на "Цветочной тропе"
        return
    
    loc = locations[location_id]
    current_time = datetime.now()
    
    # Спавн трав
    if spawn_type in [None, 'herbs']:
        last_herb_spawn = datetime.fromisoformat(loc['last_herb_spawn'])
        if current_time - last_herb_spawn >= timedelta(hours=4):
            loc['herb_count'] = 8  # Восстанавливаем до максимума
            loc['last_herb_spawn'] = current_time.isoformat()
            save_locations()
            logger.info(f"Herbs respawned to 8 at location {location_id}")
    
    # Спавн мышей
    if spawn_type in [None, 'mice']:
        last_mouse_spawn = datetime.fromisoformat(loc['last_mouse_spawn'])
        if current_time - last_mouse_spawn >= timedelta(hours=4):
            loc['mouse_count'] = 8  # Восстанавливаем до максимума
            loc['last_mouse_spawn'] = current_time.isoformat()
            save_locations()
            logger.info(f"Mice respawned to 8 at location {location_id}")

async def auto_spawn_items():
    """
    Фоновая задача для автоматического спавна ресурсов на локациях каждые 5 минут.
    """
    logger.info("Запуск фоновой задачи auto_spawn_items")
    while True:
        try:
            spawn_items(location_id=1, spawn_type=None)  # Проверяем и травы, и мышей
            logger.debug("Проверка спавна ресурсов выполнена")
            await asyncio.sleep(300)  # Проверяем каждые 5 минут (300 секунд)
        except Exception as e:
            logger.error(f"Ошибка в auto_spawn_items: {e}")

def start_auto_spawn_items():
    """
    Запускает фоновую задачу спавна ресурсов.
    """
    asyncio.create_task(auto_spawn_items())
    logger.info("Фоновая задача auto_spawn_items создана")

load_locations()