# app/item_templates.py
import json
import os

item_templates = {}

def load_item_templates():
    global item_templates
    try:
        file_path = 'app/item_templates.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            item_templates = data.get('templates', {})
            print(f"Loaded item templates: {item_templates}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading item_templates.json: {e}")
        item_templates = {
            "mouse": {
                "name": "Мышь",
                "type": "food",
                "hunger_restore": 20,
                "description": "Маленькая добыча, восстанавливает голод."
            },
            "cobweb": {
                "name": "Паутина",
                "type": "herb",
                "heal_restore": 10,
                "description": "Используется для остановки кровотечения."
            },
            "tansy": {
                "name": "Пижма",
                "type": "herb",
                "heal_restore": 5,
                "description": "Лечит кашель и снимает жар."
            }
        }
        save_item_templates()

def save_item_templates():
    with open('app/item_templates.json', 'w', encoding='utf-8') as file:
        json.dump({"templates": item_templates}, file, ensure_ascii=False, indent=4)
    print(f"Saved item templates: {item_templates}")

load_item_templates()