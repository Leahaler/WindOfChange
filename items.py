# app/items.py
import json

items = {}
item_counter = 1

def load_items():
    global items, item_counter
    try:
        with open('items.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            items = data.get('items', {})
            items = {str(key): value for key, value in items.items()}
            item_counter = data.get('item_counter', 1)
            print(f"Loaded items: {len(items)}, item_counter: {item_counter}")
    except (FileNotFoundError, json.JSONDecodeError):
        items = {}
        item_counter = 1
        save_items()

def save_items():
    global items, item_counter
    with open('items.json', 'w', encoding='utf-8') as file:
        json.dump({'items': items, 'item_counter': item_counter}, file, ensure_ascii=False, indent=4)
        print(f"Saved items: {len(items)}, item_counter: {item_counter}")

def increment_item_counter():
    global item_counter
    current_id = item_counter
    item_counter += 1
    print(f"Incremented item_counter to {item_counter}, returning {current_id}")
    save_items()
    return str(current_id)

load_items()