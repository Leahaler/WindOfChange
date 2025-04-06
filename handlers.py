
from aiogram import F, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.locations
from app.items import items, save_items, increment_item_counter
from app.item_templates import item_templates

import logging
import random
import asyncio
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

user_data = {}
id_counter = 1
items = {}
item_counter = 1
active_hunts = {}  # Для хранения задач охоты

# Классы состояний
class Reg(StatesGroup):
    name = State()

class HuntState(StatesGroup):
    hunting = State()

class MovingState(StatesGroup):
    moving = State()

def load_items():
    global items, item_counter
    try:
        with open('items.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            items = data.get('items', {})
            items = {str(key): value for key, value in items.items()}
            item_counter = data.get('item_counter', 1)
    except FileNotFoundError:
        items = {}
        item_counter = 1
        save_items()
    except json.JSONDecodeError:
        items = {}
        item_counter = 1
        save_items()

def save_items():
    with open('items.json', 'w', encoding='utf-8') as file:
        json.dump({'items': items, 'item_counter': item_counter}, file, ensure_ascii=False, indent=4)

def save_items():
    with open('items.json', 'w', encoding='utf-8') as file:
        json.dump({'items': items, 'item_counter': item_counter}, file, ensure_ascii=False, indent=4)

def load_data():
    global user_data, id_counter
    try:
        with open('user_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            user_data = data.get('user_data', {})
            id_counter = data.get('id_counter', 1)
            for user_id, user_info in user_data.items():
                if 'current_location' not in user_info:
                    user_info['current_location'] = 1
                if 'location_arrival_time' not in user_info:
                    user_info['location_arrival_time'] = datetime.now().isoformat()
                if 'inventory' not in user_info:
                    user_info['inventory'] = [None] * 5
                if 'remaining_time' not in user_info:  # Для возраста
                    user_info['remaining_time'] = 0
                if 'hunger_remaining_time' not in user_info:  # Для голода
                    user_info['hunger_remaining_time'] = 0
                if 'thirst_remaining_time' not in user_info:  # Для жажды
                    user_info['thirst_remaining_time'] = 0
                user_info['inventory'] = [
                    str(item_id) if (item_id is not None and str(item_id) in items) else None
                    for item_id in user_info['inventory']
                ]
        save_data()
    except FileNotFoundError:
        user_data = {}
        id_counter = 1
        save_data()
    except json.JSONDecodeError:
        user_data = {}
        id_counter = 1
        save_data()

def save_data():
    with open('user_data.json', 'w', encoding='utf-8') as file:
        json.dump({'user_data': user_data, 'id_counter': id_counter}, file, ensure_ascii=False, indent=4)

def update_state(user_id):
    if user_id in user_data:
        last_update = datetime.fromisoformat(user_data[user_id]['last_update'])
        time_passed = datetime.now() - last_update
        remaining_time = user_data[user_id].get('remaining_time', 0)
        total_time_passed = time_passed.total_seconds() + remaining_time
        hours_passed = int(total_time_passed // 3600)
        if hours_passed > 0:
            user_data[user_id]['age'] += hours_passed * 0.0104167
        remaining_time = int(total_time_passed % 3600)
        user_data[user_id]['remaining_time'] = remaining_time
        user_data[user_id]['last_update'] = datetime.now().isoformat()
        save_data()

clan1 = 'красный'
clan2 = 'синий'
clan3 = 'желтый'
clan4 = 'зеленый'

position1 = 'Цветочек'
position2 = 'Жена'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f'Привет! \nТвой айди: {message.from_user.id}\nИмя: {message.from_user.first_name}')




@router.message(Command('профиль'))
async def profile_command(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /профиль и вызывает отображение профиля.

    Args:
        message (Message): Сообщение с командой
        state (FSMContext): Контекст состояния FSM

    Returns:
        None
    """
    user_id = str(message.from_user.id)
    update_state(user_id)  # Обновляем онлайн-статус
    await show_profile_from_message(message, state, user_id)


async def show_profile_from_message(message: Message, state: FSMContext, user_id: str) -> None:
    """
    Отображает профиль пользователя для команд и текстовых сообщений.
    """
    current_state = await state.get_state()
    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await message.answer("Вы заняты! Завершите текущее действие.")
        return

    update_state(user_id)
    if user_id not in user_data:
        await message.answer('Вы не зарегистрированы!')
        return

    user_info = user_data[user_id]
    current_location = user_info['current_location']
    
    # Подсчитываем занятые слоты в инвентаре
    inventory = user_info.get('inventory', [None, None, None, None, None])
    occupied_slots = sum(1 for slot in inventory if slot is not None)
    inventory_display = f"Инвентарь: {occupied_slots}/5"

    profile_text = f"""
——— {user_info['name']} ———
id: {user_info['id']}
Пол: {user_info['sex']}
Возраст: {user_info['age']:.2f} лун
Клан: {user_info['clan_cat']}
Должность: {user_info['position_cat']}
————————— 
Боевой опыт: {user_info['combat_exp_cat']}
Охотничий опыт: {user_info['hunt_exp_cat']}
Знахарский опыт: {user_info['heal_exp_cat']}
Плавательный опыт: {user_info['swim_exp_cat']}
Лазательный опыт: {user_info['climb_exp_cat']}
————————— 
Здоровье: {user_info['heal_point_cat']}/100
Жажда: {user_info['thirst_cat']}/100
Голод: {user_info['hunger_cat']}/100
{inventory_display}
    """
    await message.answer(profile_text, reply_markup=await kb.profile_buttons(current_location))

@router.callback_query(F.data == 'show_profile')
async def show_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает нажатие inline-кнопки "Профиль" и отображает профиль пользователя.
    """
    current_state = await state.get_state()
    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await callback.answer("Вы заняты! Завершите текущее действие.")
        return

    user_id = str(callback.from_user.id)
    update_state(user_id)
    if user_id not in user_data:
        await callback.message.answer('Вы не зарегистрированы!')
        await callback.answer()
        return

    user_info = user_data[user_id]
    current_location = user_info['current_location']
    
    # Подсчитываем занятые слоты в инвентаре
    inventory = user_info.get('inventory', [None, None, None, None, None])
    occupied_slots = sum(1 for slot in inventory if slot is not None)
    inventory_display = f"Инвентарь: {occupied_slots}/5"

    profile_text = f"""
——— {user_info['name']} ———
id: {user_info['id']}
Пол: {user_info['sex']}
Возраст: {user_info['age']:.2f} лун
Клан: {user_info['clan_cat']}
Должность: {user_info['position_cat']}
————————— 
Боевой опыт: {user_info['combat_exp_cat']}
Охотничий опыт: {user_info['hunt_exp_cat']}
Знахарский опыт: {user_info['heal_exp_cat']}
Плавательный опыт: {user_info['swim_exp_cat']}
Лазательный опыт: {user_info['climb_exp_cat']}
————————— 
Здоровье: {user_info['heal_point_cat']}/100
Жажда: {user_info['thirst_cat']}/100
Голод: {user_info['hunger_cat']}/100
{inventory_display}
    """
    try:
        await callback.message.answer(profile_text, reply_markup=await kb.profile_buttons(current_location))
        await callback.answer()
    except TelegramBadRequest:
        await callback.message.answer("Запрос устарел. Попробуйте снова.")


@router.callback_query(F.data == 'show_inventory')
async def show_inventory(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    inventory = user_data[user_id].get('inventory', [None, None, None, None, None])
    occupied_slots = sum(1 for slot in inventory if slot is not None)

    items_list = []
    for item_id in inventory:
        if item_id is not None:
            if item_id in items:
                template_id = items[item_id]['template']
                template = app.item_templates.item_templates.get(template_id, {"name": "Неизвестный предмет"})
                items_list.append(f"{template['name']} (id{item_id})")
            else:
                logger.warning(f"Предмет с ID {item_id} не найден в items для пользователя {user_id}")
                items_list.append(f"Неизвестный предмет (id{item_id})")

    inventory_text = "——— Инвентарь ———\n"
    if items_list:
        inventory_text += "\n".join(items_list)
    else:
        inventory_text += "Ваш инвентарь пуст."

    inventory_text += f"\nЗанято слотов: {occupied_slots}/5"

    try:
        await callback.message.answer(inventory_text, reply_markup=await kb.profile_buttons(user_data[user_id]['current_location']))
        await callback.answer()
    except TelegramBadRequest:
        await callback.message.answer("Запрос устарел. Попробуйте снова.")



@router.message(Command('help')) #команда старт
async def get_help(message: Message): #асинхронная функция
    user_id = str(message.from_user.id)
    update_state(user_id) 
    await message.answer(f'На данный момент есть такие команды: \n/регистрация\n/профиль\n/игроки\n/онлайн')

@router.message(Command('удалить'))
async def remove_buttons(message: types.Message):
    await message.answer("Ккнопок нет", reply_markup=types.ReplyKeyboardRemove())

@router.message(Command('регистрация'))
async def reg_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id in user_data:
        await message.answer('Вы уже зарегистрированы!')
    else:
        await message.answer('Выберите племя вашего персонажа', reply_markup= await kb.choose_clan())

@router.callback_query(F.data.in_(['clan1', 'clan2', 'clan3', 'clan4']))
async def choose_clan(callback: CallbackQuery, state: FSMContext):
    global clan1, clan2, clan3, clan4
    user_id = str(callback.from_user.id)
    if callback.data == 'clan1':
        chosen_clan = clan1
    elif callback.data == 'clan2':
        chosen_clan = clan2
    elif callback.data == 'clan3':
        chosen_clan = clan3
    elif callback.data == 'clan4':
        chosen_clan = clan4

    await state.update_data(chosen_clan=chosen_clan)  # Сохраняем выбранный клан в состоянии
    await callback.answer()
    await callback.message.answer('Выберите пол вашего персонажа', reply_markup=await kb.choose_sex())

@router.callback_query(F.data.in_(['sex_male', 'sex_female']))
async def choose_gender(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    gender = "Кот" if callback.data == 'sex_male' else "Кошка"
    
    # Сохраняем пол в состоянии
    await state.update_data(gender=gender)
    
    await callback.answer()
    await callback.message.answer('Введите ваше имя')
    
    # Устанавливаем состояние ожидания имени
    await state.set_state(Reg.name)  # Устанавливаем состояние

    
@router.message(Reg.name)
async def reg_two(message: Message, state: FSMContext):
    global id_counter, user_data, position1
    user_id = str(message.from_user.id)
    update_state(user_id)
    user_info = await state.get_data()
    gender = user_info.get('gender')
    chosen_clan = user_info.get('chosen_clan')

    if user_id not in user_data:
        user_data[user_id] = {
            'id': id_counter,
            'name': message.text,
            'username': message.from_user.username if message.from_user.username else None,
            'age': 0.0,
            'sex': gender,
            'position_cat': position1,
            'clan_cat': chosen_clan,
            'combat_exp_cat': 0,
            'hunt_exp_cat': 0,
            'heal_exp_cat': 0,
            'swim_exp_cat': 0,
            'climb_exp_cat': 0,
            'heal_point_cat': 100,
            'thirst_cat': 100,
            'hunger_cat': 100,
            'last_update': datetime.now().isoformat(),
            'current_location': 1,
            'location_arrival_time': datetime.now().isoformat(),
            'inventory': [None, None, None, None, None]  # 5 слотов
        }
        id_counter += 1
        save_data()
        await message.answer(f'Ваше имя: {message.text}\nID: {user_data[user_id]["id"]}\nПол: {gender}')
        await state.clear()
    else:
        await message.answer('Вы уже зарегистрированы!')

from datetime import datetime

@router.message(Command('игроки'))
async def players_command(message: Message):
    update_state(user_id) 

    # Итерируемся по зарегистрированным пользователям
    for user_id, user_info in user_data.items():
        name = user_info.get('name', 'Имя неизвестно')  # Значение по умолчанию
        clan = user_info.get('clan_cat', 'Племя неизвестно')  # Значение по умолчанию
        game_id = user_info.get('id', 'ID неизвестно')  # Получаем игровое ID

        # Создаем упоминание пользователя
        mention = f"[{name}](tg://user?id={user_id})"
        players_list.append(f'Игровой ID: {game_id}, Имя: {mention}, Племя: {clan}')

    if players_list:
        players_output = '\n'.join(players_list)  # Формируем итоговую строку из списка
        await message.answer(f'Список игроков:\n{players_output}', parse_mode='MarkdownV2')
    else:
        await message.answer('Нет зарегистрированных игроков!')
'''
@router.message(Command('онлайн'))
async def players_command(message: Message):
    user_id = str(message.from_user.id)
    update_state(user_id) 
    players_list = []
    current_time = datetime.now()

    # Итерируемся по зарегистрированным пользователям
    for user_id, user_info in user_data.items():
        last_update = datetime.strptime(user_info['last_update'], '%Y-%m-%d %H:%M:%S')

        # Проверяем, обновлялся ли игрок менее 15 минут назад
        if current_time - last_update < timedelta(minutes=15):
            name = user_info.get('name', 'Имя неизвестно')  # Значение по умолчанию
            clan = user_info.get('clan_cat', 'Племя неизвестно')  # Значение по умолчанию
            game_id = user_info.get('id', 'ID неизвестно')  # Получаем игровое ID

            # Создаем упоминание пользователя
            mention = f"[{name}](tg://user?id={user_id})"
            players_list.append(f'Игровой ID: {game_id}, Имя: {mention}, Племя: {clan}')

    if players_list:
        players_output = '\n'.join(players_list)  # Формируем итоговую строку из списка
        await message.answer(f'Список игроков:\n{players_output}', parse_mode='MarkdownV2')
    else:
        await message.answer('Нет онлайн игроков')
'''

@router.message(Command('update_players'))
async def update_players_command(message: Message):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    age = 2.4479245  # Задайте нужный возраст

    for user_id, user_info in user_data.items():
        user_info['last_update'] = current_time  # Обновляем последний апдейт
        user_info['age'] = age  # Устанавливаем возраст

    await message.answer('Данные всех игроков обновлены!')
    save_data()

@router.message(Command('локация'))
async def get_location(message: Message, state: FSMContext) -> None:
    user_id = str(message.from_user.id)
    update_state(user_id)
    current_location_id = user_data[user_id]['current_location']
    
    if current_location_id not in app.locations.locations:
        await message.answer(f"Локация ID {current_location_id} не существует!")
        return
    
    loc_info = app.locations.locations[current_location_id]
    
    # Подсчитываем котов поблизости
    current_time = datetime.now()
    nearby_cats = sum(
        1 for uid, user_info in user_data.items()
        if user_info['current_location'] == current_location_id
        and current_time - datetime.fromisoformat(user_info['last_update']) < timedelta(minutes=15)
    )
    
    # Подсчитываем предметы на земле
    dropped_items_count = len(loc_info.get('dropped_items', []))
    
    location_text = (
        f"——— {loc_info['name']} ———\n\n"
        f"Поблизости {nearby_cats} котов и {dropped_items_count} предметов\n\n"
        f"{loc_info['description']}"
    )
    if loc_info['temperature'] is not None:
        location_text += f"\nТемпература: {loc_info['temperature']}°C"
    if loc_info['weather'] is not None:
        location_text += f"\nПогода: {loc_info['weather']}"
    
    await message.answer(location_text, reply_markup=await kb.location_buttons(current_location_id))

@router.message(lambda message: message.text.lower() == "л")
async def show_location_shortcut(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    logger.info(f"Вызвана команда 'л' для user_id: {user_id}")
    
    # Проверяем, зарегистрирован ли пользователь
    if user_id not in user_data:
        logger.warning(f"Пользователь {user_id} не зарегистрирован")
        await message.answer("Вы не зарегистрированы! Используйте /регистрация.")
        return

    update_state(user_id)
    current_location = user_data[user_id]['current_location']
    
    # Временная совместимость с названиями локаций
    if isinstance(current_location, str):
        location_name_to_id = {loc['name']: loc_id for loc_id, loc in app.locations.locations.items()}
        current_location_id = location_name_to_id.get(current_location, 1)
        user_data[user_id]['current_location'] = current_location_id
        save_data()
        logger.info(f"Конверсия локации для {user_id}: {current_location} -> {current_location_id}")
    else:
        current_location_id = current_location

    loc_info = app.locations.locations[current_location_id]
    
    # Подсчитываем котов поблизости
    current_time = datetime.now()
    nearby_cats = sum(
        1 for uid, user_info in user_data.items()
        if user_info['current_location'] == current_location_id
        and current_time - datetime.fromisoformat(user_info['last_update']) < timedelta(minutes=15)
    )
    
    # Подсчитываем предметы на земле
    dropped_items_count = len(loc_info.get('dropped_items', []))
    
    location_text = (
        f"——— {loc_info['name']} ———\n\n"
        f"Поблизости {nearby_cats} котов и {dropped_items_count} предметов\n\n"
        f"{loc_info['description']}"
    )
    if loc_info['temperature'] is not None:
        location_text += f"\nТемпература: {loc_info['temperature']}°C"
    if loc_info['weather'] is not None:
        location_text += f"\nПогода: {loc_info['weather']}"

    logger.info(f"Отображаем локацию для {user_id}: {loc_info['name']}")
    await message.answer(
        location_text,
        reply_markup=await kb.location_buttons(current_location_id)
    )

@router.callback_query(F.data == 'roads')
async def show_transitions(callback: CallbackQuery, state: FSMContext):
    """
    Показывает доступные переходы для текущей локации.
    """
    current_state = await state.get_state()
    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await callback.answer("Вы заняты! Завершите текущее действие.")
        return

    user_id = str(callback.from_user.id)
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    current_location = user_data[user_id]['current_location']

    # Временная совместимость с названиями локаций
    if isinstance(current_location, str):
        location_name_to_id = {loc['name']: loc_id for loc_id, loc in locations.items()}
        current_location_id = location_name_to_id.get(current_location, 1)
        user_data[user_id]['current_location'] = current_location_id
        save_data()
        logger.info(f"Конверсия локации для {user_id}: {current_location} -> {current_location_id}")
    else:
        current_location_id = current_location

    try:
        await callback.message.answer(
            "Куда вы хотите перейти?",
            reply_markup=await kb.transition_buttons(current_location_id)
        )
        await callback.answer()
    except TelegramBadRequest:
        await callback.message.answer("Запрос устарел. Попробуйте снова.")
        logger.warning("TelegramBadRequest в show_transitions")


@router.callback_query(F.data.startswith('move_to_'))
async def start_moving(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    current_state = await state.get_state()
    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await callback.answer("Вы заняты! Завершите текущее действие.")
        return

    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    target_location_id = int(callback.data.replace('move_to_', ''))
    current_location = user_data[user_id]['current_location']

    if isinstance(current_location, str):
        location_name_to_id = {loc['name']: loc_id for loc_id, loc in app.locations.locations.items()}
        current_location_id = location_name_to_id.get(current_location, 1)
        user_data[user_id]['current_location'] = current_location_id
        save_data()
    else:
        current_location_id = current_location

    # Используем app.locations.locations вместо locations
    if target_location_id in app.locations.locations[current_location_id]['adjacent']:
        await state.set_state(MovingState.moving)
        await state.update_data(target_location_id=target_location_id)
        try:
            await callback.message.answer(
                "Переход займет 20 секунд.",
                reply_markup=await kb.cancel_button()
            )
            await callback.answer()
        except TelegramBadRequest:
            await callback.message.answer("Запрос устарел. Попробуйте снова.")
            await state.clear()
            return

        async def move_task():
            try:
                await asyncio.sleep(20)
                current_state = await state.get_state()
                if current_state == MovingState.moving.state:
                    user_data[user_id]['current_location'] = target_location_id
                    user_data[user_id]['location_arrival_time'] = datetime.now().isoformat()
                    save_data()
                    loc_info = app.locations.locations[target_location_id]  # Здесь тоже исправлено
                    location_text = f"——— {loc_info['name']} ———\n\n{loc_info['description']}"
                    if loc_info['temperature'] is not None:
                        location_text += f"\nТемпература: {loc_info['temperature']}°C"
                    if loc_info['weather'] is not None:
                        location_text += f"\nПогода: {loc_info['weather']}"
                    await callback.message.answer(
                        location_text,
                        reply_markup=await kb.location_buttons(target_location_id)
                    )
                    await state.clear()
            except asyncio.CancelledError:
                pass

        asyncio.create_task(move_task())
    else:
        await callback.message.answer("Вы не можете перейти в эту локацию отсюда!")
        await callback.answer()

def escape_markdown_v2(text):
    """Экранирует зарезервированные символы для MarkdownV2."""
    reserved_chars = r'_*\[\]()~`#+-=|{}.!'
    for char in reserved_chars:
        text = text.replace(char, f'\\{char}')
    return text



@router.callback_query(F.data == 'look_around')
async def look_around(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await callback.answer("Вы заняты! Завершите текущее действие.")
        return

    user_id = str(callback.from_user.id)
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    update_state(user_id)
    current_location_id = user_data[user_id]['current_location']
    
    if current_location_id not in app.locations.locations:
        await callback.message.answer(f"Локация ID {current_location_id} не существует!")
        await callback.answer()
        return

    players_list = []
    current_time = datetime.now()

    current_username = callback.from_user.username
    if user_id in user_data and user_data[user_id].get('username') != current_username:
        user_data[user_id]['username'] = current_username
        user_data[user_id]['last_update'] = datetime.now().isoformat()
        save_data()

    for uid, user_info in user_data.items():
        if user_info['current_location'] == current_location_id:
            last_update = datetime.fromisoformat(user_info['last_update'])
            if current_time - last_update < timedelta(minutes=15):
                name = user_info.get('name', 'Имя неизвестно')
                clan = user_info.get('clan_cat', 'Племя неизвестно')
                game_id = str(user_info.get('id', 'ID неизвестно'))
                position_cat = user_info.get('position_cat', 'Должность неизвестна')
                username = user_info.get('username')
                arrival_time = user_info.get('location_arrival_time', datetime.now().isoformat())
                player_info = f"{name} (id{game_id}, {clan}, {position_cat}, @{username})" if username else f"{name} (id{game_id}, {clan}, {position_cat})"
                players_list.append({'text': player_info, 'arrival_time': datetime.fromisoformat(arrival_time)})

    players_list.sort(key=lambda x: x['arrival_time'])
    players_message = '\n'.join(player['text'] for player in players_list) if players_list else "Никого нет поблизости."
    
    dropped_items = app.locations.locations[current_location_id].get('dropped_items', [])
    items_message = '\n'.join(
        f"{item_templates[items[item_id]['template']]['name']} (id{item_id})" 
        for item_id in dropped_items 
        if item_id in items and items[item_id]['template'] in item_templates
    ) if dropped_items else "На земле ничего нет."
    
    loc_info = app.locations.locations[current_location_id]
    resource_message = f"Доступно трав: {loc_info['herb_count']}\nДоступно дичи: {loc_info['mouse_count']}"
    
    message_text = (
        f"——— Коты поблизости  ———\n"
        f"{players_message}\n"
        f"——— Ресурсы ———\n"
        f"{resource_message}\n"
        f"——— Предметы на земле ———\n"
        f"{items_message}"
    )
    await callback.message.answer(message_text)
    await callback.answer()


@router.callback_query(F.data == 'show_actions')
async def show_actions(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return
    
    current_location_id = user_data[user_id]['current_location']
    try:
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=await kb.action_buttons(current_location_id)
        )
        await callback.answer()
    except TelegramBadRequest:
        await callback.message.answer("Запрос устарел. Попробуйте снова.")

async def action_buttons(current_location_id):
    """
    Создает клавиатуру с доступными действиями для текущей локации.
    """
    logger.info(f"Формируем действия для локации ID: {current_location_id}, тип: {type(current_location_id)}")
    keyboard = InlineKeyboardBuilder()
    
    # Приводим current_location_id к int, если это строка
    try:
        location_id = int(current_location_id)
    except (ValueError, TypeError):
        logger.error(f"Некорректный ID локации: {current_location_id}")
        location_id = 1  # Дефолтное значение
    
    if location_id == 1:  # "Цветочная тропинка"
        keyboard.add(InlineKeyboardButton(text="Охота", callback_data="start_hunt"))
        logger.info("Добавлена кнопка 'Охота'")
    else:
        logger.info(f"Кнопка 'Охота' не добавлена, локация ID {location_id} не подходит")
    
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back_to_location"))
    markup = keyboard.adjust(1).as_markup()
    logger.info(f"Готовая клавиатура: {markup.inline_keyboard}")
    return markup



# Обновляем обработчик охоты
active_hunts = {}  # Глобальный словарь для хранения задач

active_hunts = {}

# Обработчик охоты
@router.callback_query(F.data == 'start_hunt')
async def start_hunt(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    update_state(user_id)
    current_state = await state.get_state()
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    current_location_id = user_data[user_id]['current_location']
    if current_location_id != 1:
        await callback.answer("Охота доступна только на Цветочной тропинке!")
        return

    # Проверяем и обновляем спавн мышей
    app.locations.spawn_items(current_location_id, spawn_type='mice')
    if app.locations.locations[current_location_id]['mouse_count'] <= 0:
        await callback.answer("Мыши на этой локации закончились!")
        return

    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await callback.answer("Вы заняты! Завершите текущее действие.")
        return

    await state.set_state(HuntState.hunting)
    try:
        await callback.message.answer(
            "Вы начали охоту, она продлится 3 минуты.",
            reply_markup=await kb.cancel_button()
        )
        await callback.answer()
    except Exception:
        await callback.message.answer("Запрос устарел. Попробуйте снова.")
        await state.clear()
        return

    async def hunt_task():
        try:
            await asyncio.sleep(2)  # 3 минуты
            current_state = await state.get_state()
            if current_state == HuntState.hunting.state:
                success = random.choice([True, True, True, True, False])
                if success and app.locations.locations[current_location_id]['mouse_count'] > 0:
                    print(f"Creating new mouse for user {user_id} at location {current_location_id}")
                    new_item_id = increment_item_counter()  # Создаём новый ID
                    print(f"New mouse created with ID: {new_item_id}")
                    items[new_item_id] = {"template": "mouse"}
                    save_items()  # Сохраняем новый предмет

                    inventory = user_data[user_id]['inventory']
                    free_slot = next((i for i, slot in enumerate(inventory) if slot is None), None)
                    app.locations.locations[current_location_id]['mouse_count'] -= 1
                    app.locations.save_locations()

                    if free_slot is not None:
                        inventory[free_slot] = new_item_id
                        await callback.message.answer(
                            f"Вы поймали мышь! Ваши охотничьи навыки выросли на 2 ед. (id{new_item_id})"
                        )
                    else:
                        if 'dropped_items' not in app.locations.locations[current_location_id]:
                            app.locations.locations[current_location_id]['dropped_items'] = []
                        app.locations.locations[current_location_id]['dropped_items'].append(new_item_id)
                        app.locations.save_locations()
                        await callback.message.answer(
                            f"Вы поймали мышь, но инвентарь полон! Она упала на пол. (id{new_item_id})"
                        )
                    user_data[user_id]['hunt_exp_cat'] += 2
                    save_data()
                else:
                    await callback.message.answer("Вы ничего не поймали.")
                await state.clear()
        except asyncio.CancelledError:
            print(f"Hunt task cancelled for user {user_id}")
            pass

    task = asyncio.create_task(hunt_task())
    active_hunts[user_id] = task

@router.callback_query(F.data == 'cancel_button')
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await callback.answer("Вам нечего отменять.")
        return
    
    user_id = str(callback.from_user.id)
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    # Отменяем задачу охоты, если она существует
    if user_id in active_hunts:
        active_hunts[user_id].cancel()
        del active_hunts[user_id]
    
    current_location_id = user_data[user_id]['current_location']
    # Используем app.locations.locations вместо locations
    loc_info = app.locations.locations[current_location_id]
    
    try:
        await callback.message.answer("Вы отменили действие.")
        location_text = f"——— {loc_info['name']} ———\n\n{loc_info['description']}"
        if loc_info['temperature'] is not None:
            location_text += f"\nТемпература: {loc_info['temperature']}°C"
        if loc_info['weather'] is not None:
            location_text += f"\nПогода: {loc_info['weather']}"
        
        await callback.message.answer(
            location_text,
            reply_markup=await kb.location_buttons(current_location_id)
        )
        await callback.answer()  # Немедленный ответ
    except TelegramBadRequest:
        await callback.message.answer("Запрос устарел. Попробуйте снова.")
    
    await state.clear()
    

@router.message(lambda message: message.text.lower() == "п")
async def profile_shortcut(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает сообщение "п" и вызывает отображение профиля.

    Args:
        message (Message): Сообщение с текстом "п"
        state (FSMContext): Контекст состояния FSM

    Returns:
        None
    """
    user_id = str(message.from_user.id)
    update_state(user_id)  # Обновляем онлайн-статус
    await show_profile_from_message(message, state, user_id)


@router.callback_query(F.data == 'show_profile')
async def show_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает нажатие inline-кнопки "Профиль" и отображает профиль пользователя.

    Args:
        callback (CallbackQuery): Объект обратного вызова от кнопки
        state (FSMContext): Контекст состояния FSM

    Returns:
        None
    """
    current_state = await state.get_state()
    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await callback.answer("Вы заняты! Завершите текущее действие.")
        return

    user_id = str(callback.from_user.id)
    update_state(user_id)
    if user_id not in user_data:
        await callback.message.answer('Вы не зарегистрированы!')
        await callback.answer()
        return

    user_info = user_data[user_id]
    current_location = user_info['current_location']
    profile_text = f"""
——— {user_info['name']} ———
id: {user_info['id']}
Пол: {user_info['sex']}
Возраст: {user_info['age']:.2f} лун
Клан: {user_info['clan_cat']}
Должность: {user_info['position_cat']}
————————— 
Боевой опыт: {user_info['combat_exp_cat']}
Охотничий опыт: {user_info['hunt_exp_cat']}
Знахарский опыт: {user_info['heal_exp_cat']}
Плавательный опыт: {user_info['swim_exp_cat']}
Лазательный опыт: {user_info['climb_exp_cat']}
————————— 
Здоровье: {user_info['heal_point_cat']}/100
Жажда: {user_info['thirst_cat']}/100
Голод: {user_info['hunger_cat']}/100
    """
    await callback.message.answer(profile_text, reply_markup=await kb.profile_buttons(current_location))
    await callback.answer()


@router.callback_query(F.data == 'back_to_location')
async def back_to_location(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    update_state(user_id)
    current_location_id = user_data[user_id]['current_location']
    
    if current_location_id not in app.locations.locations:
        await callback.message.answer(f"Локация ID {current_location_id} не существует!")
        await callback.answer()
        return

    loc_info = app.locations.locations[current_location_id]
    message_text = (
        f"{loc_info['name']}\n"
        f"{loc_info['description']}\n\n"
        f"Температура: {loc_info['temperature']}°C\n"
        f"Погода: {loc_info['weather']}"
    )
    await callback.message.answer(message_text, reply_markup=await kb.location_buttons(current_location_id))
    await callback.answer()

@router.message(Command('чат'))
async def send_chat_message(message: types.Message) -> None:
    """
    Обрабатывает команду /чат и отправляет сообщение всем онлайн-игрокам на текущей локации.
    В сообщении указывается имя отправителя и в скобках: ID, клан, должность и @username (если есть).

    Args:
        message (types.Message): Сообщение с командой /чат и текстом

    Returns:
        None
    """
    user_id = str(message.from_user.id)
    update_state(user_id)  # Обновляем онлайн-статус
    
    # Проверяем, что после команды есть текст
    if not message.text.strip().startswith('/чат '):
        await message.answer("Используйте: /чат <текст>")
        return
    
    # Извлекаем текст сообщения (убираем "/чат ")
    chat_text = message.text[5:].strip()
    if not chat_text:
        await message.answer("Введите текст сообщения после /чат!")
        return
    
    current_location = user_data[user_id]['current_location']
    sender_info = user_data[user_id]
    sender_name = sender_info.get('name', 'Имя неизвестно')
    sender_id = str(sender_info.get('id', 'ID неизвестно'))
    sender_clan = sender_info.get('clan_cat', 'Племя неизвестно')
    sender_position = sender_info.get('position_cat', 'Должность неизвестна')
    sender_username = sender_info.get('username')  # Получаем юзернейм
    
    # Формируем сообщение с юзернеймом в скобках в конце, если он есть
    if sender_username:
        formatted_message = f"{sender_name} (id{sender_id}, {sender_clan}, {sender_position}, @{sender_username}): {chat_text}"
    else:
        formatted_message = f"{sender_name} id{sender_id}, {sender_clan}, {sender_position}): {chat_text}"
    
    # Собираем список игроков на текущей локации, которые в сети (кроме отправителя)
    current_time = datetime.now()
    recipients = []
    for uid, user_info in user_data.items():
        if (uid != user_id and 
            user_info['current_location'] == current_location and 
            current_time - datetime.fromisoformat(user_info['last_update']) < timedelta(minutes=15)):
            recipients.append(uid)
    
    # Отправляем сообщение каждому игроку в сети
    for recipient_id in recipients:
        try:
            await message.bot.send_message(
                chat_id=recipient_id,
                text=formatted_message
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {recipient_id}: {e}")
    
    # Подтверждаем отправителю, что сообщение отправлено
    await message.answer("Сообщение отправлено.")

@router.message(Command('update_usernames'))
async def update_usernames(message: Message):
    """
    Обновляет юзернеймы всех игроков в базе данных.

    Args:
        message (Message): Сообщение с командой
    """
    user_id = str(message.from_user.id)
    if user_id in user_data:  # Простая проверка прав (можно усилить)
        for uid in user_data.keys():
            # Здесь нужен доступ к актуальному юзернейму, но без API-запроса это невозможно
            # Предположим, что это делается вручную или через другой механизм
            pass
        save_data()
        await message.answer("Юзернеймы обновлены (требуется ручное обновление для старых данных).")
    else:
        await message.answer("Вы не зарегистрированы!")
   


@router.message(F.text.startswith("/поднять "))
async def pick_up_item(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Вы не зарегистрированы!")
        return

    try:
        item_id = message.text.split()[1]
        current_location_id = user_data[user_id]['current_location']
        
        if current_location_id not in app.locations.locations:
            await message.answer(f"Локация ID {current_location_id} не существует!")
            return
        
        if item_id not in items:
            await message.answer(f"Предмет id{item_id} не существует!")
            return
        
        if item_id not in app.locations.locations[current_location_id].get('dropped_items', []):
            await message.answer(f"Предмет id{item_id} не находится на этой локации!")
            return

        inventory = user_data[user_id]['inventory']
        free_slot = next((i for i, slot in enumerate(inventory) if slot is None), None)
        if free_slot is None:
            await message.answer("Ваш инвентарь полон!")
            return
        
        inventory[free_slot] = item_id
        app.locations.locations[current_location_id]['dropped_items'].remove(item_id)
        save_data()
        app.locations.save_locations()
        template = app.item_templates.item_templates[items[item_id]['template']]
        await message.answer(f"Вы подняли {template['name']} (id{item_id})")
    except IndexError:
        await message.answer("Укажите id предмета! Пример: /поднять 1")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)} (тип: {type(e).__name__})")

@router.message(F.text.startswith("/положить "))
async def drop_item(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Вы не зарегистрированы!")
        return

    try:
        item_id = message.text.split()[1]
        inventory = user_data[user_id]['inventory']
        current_location_id = user_data[user_id]['current_location']
        
        if current_location_id not in app.locations.locations:
            await message.answer(f"Локация ID {current_location_id} не существует!")
            return
        
        if item_id not in inventory:
            await message.answer(f"Предмет id{item_id} не находится в вашем инвентаре! Инвентарь: {inventory}")
            return
        
        if item_id not in items:
            await message.answer(f"Предмет id{item_id} не существует в базе предметов!")
            return

        slot = inventory.index(item_id)
        inventory[slot] = None
        if 'dropped_items' not in app.locations.locations[current_location_id]:
            app.locations.locations[current_location_id]['dropped_items'] = []
        app.locations.locations[current_location_id]['dropped_items'].append(item_id)
        save_data()
        app.locations.save_locations()
        template = app.item_templates.item_templates[items[item_id]['template']]
        await message.answer(f"Вы положили {template['name']} (id{item_id}) на пол")
    except IndexError:
        await message.answer("Укажите id предмета! Пример: /положить 1")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)} (тип: {type(e).__name__})")

@router.message(F.text.startswith("/положить "))
async def drop_item(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        await message.answer("Вы не зарегистрированы!")
        return

    try:
        item_id = message.text.split()[1]
        inventory = user_data[user_id]['inventory']
        current_location_id = user_data[user_id]['current_location']
        
        if current_location_id not in app.locations.locations:
            await message.answer(f"Локация ID {current_location_id} не существует!")
            return
        
        if item_id not in inventory:
            await message.answer(f"Предмет id{item_id} не находится в вашем инвентаре! Инвентарь: {inventory}")
            return
        
        if item_id not in items:
            await message.answer(f"Предмет id{item_id} не существует в базе предметов!")
            return

        slot = inventory.index(item_id)
        inventory[slot] = None
        if 'dropped_items' not in app.locations.locations[current_location_id]:
            app.locations.locations[current_location_id]['dropped_items'] = []
        app.locations.locations[current_location_id]['dropped_items'].append(item_id)
        save_data()
        app.locations.save_locations()
        template = app.item_templates.item_templates[items[item_id]['template']]
        await message.answer(f"Вы положили {template['name']} (id{item_id}) на пол")
    except IndexError:
        await message.answer("Укажите id предмета! Пример: /положить 1")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)} (тип: {type(e).__name__})")

@router.message(Command('удалиться'))
async def delete_profile(message: Message, state: FSMContext):
    """
    Удаляет профиль пользователя из базы данных, позволяя зарегистрироваться заново.
    """
    user_id = str(message.from_user.id)
    
    # Проверяем, зарегистрирован ли пользователь
    if user_id not in user_data:
        await message.answer("Вы не зарегистрированы, нечего удалять!")
        return
    
    # Удаляем пользователя из базы
    del user_data[user_id]
    save_data()
    
    # Очищаем состояние, если оно есть
    await state.clear()
    
    # Уведомляем пользователя
    await message.answer("Ваш профиль успешно удалён! Теперь вы можете зарегистрироваться заново с помощью /регистрация.")
    
    logger.info(f"Пользователь {user_id} удалил свой профиль.")

@router.callback_query(F.data == 'start_gather_herbs')
async def start_gather_herbs(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = str(callback.from_user.id)
    update_state(user_id)
    current_state = await state.get_state()
    if user_id not in user_data:
        await callback.message.answer("Вы не зарегистрированы!")
        await callback.answer()
        return

    current_location_id = user_data[user_id]['current_location']
    if current_location_id != 1:
        await callback.answer("Собирать травы можно только на Цветочной тропе!")
        return

    # Проверяем и обновляем спавн трав
    app.locations.spawn_items(current_location_id, spawn_type='herbs')
    if app.locations.locations[current_location_id]['herb_count'] <= 0:
        await callback.answer("Травы на этой локации закончились!")
        return

    if current_state in [HuntState.hunting.state, MovingState.moving.state]:
        await callback.answer("Вы заняты! Завершите текущее действие.")
        return

    await state.set_state(HuntState.hunting)
    try:
        await callback.message.answer(
            "Вы начали сбор трав, это займёт 3 минуты.",
            reply_markup=await kb.cancel_button()
        )
        await callback.answer()
    except Exception:
        await callback.message.answer("Запрос устарел. Попробуйте снова.")
        await state.clear()
        return

    async def gather_herbs_task():
        try:
            await asyncio.sleep(180)  # 3 минуты
            current_state = await state.get_state()
            if current_state == HuntState.hunting.state:
                success = random.random() < 0.8
                if success and app.locations.locations[current_location_id]['herb_count'] > 0:
                    print(f"Creating new herb for user {user_id} at location {current_location_id}")
                    new_item_id = increment_item_counter()  # Создаём новый ID
                    herb = random.choice(["tansy", "cobweb"])
                    items[new_item_id] = {"template": herb}
                    save_items()  # Сохраняем новый предмет
                    print(f"New herb created with ID: {new_item_id}, type: {herb}")

                    inventory = user_data[user_id]['inventory']
                    free_slot = next((i for i, slot in enumerate(inventory) if slot is None), None)
                    herb_name = item_templates[herb]['name']
                    app.locations.locations[current_location_id]['herb_count'] -= 1
                    app.locations.save_locations()

                    if free_slot is not None:
                        inventory[free_slot] = new_item_id
                        await callback.message.answer(
                            f"Вы собрали {herb_name}! Ваш знахарский опыт вырос на 2 ед. (ID: {new_item_id})"
                        )
                    else:
                        if 'dropped_items' not in app.locations.locations[current_location_id]:
                            app.locations.locations[current_location_id]['dropped_items'] = []
                        app.locations.locations[current_location_id]['dropped_items'].append(new_item_id)
                        app.locations.save_locations()
                        await callback.message.answer(
                            f"Вы собрали {herb_name}, но инвентарь полон! Она упала на пол. (ID: {new_item_id})"
                        )
                    user_data[user_id]['heal_exp_cat'] += 2
                    save_data()
                else:
                    await callback.message.answer("Вы не нашли никаких трав.")
                await state.clear()
        except asyncio.CancelledError:
            print(f"Gather herbs task cancelled for user {user_id}")
            pass
        except Exception as e:
            logger.error(f"Error in gather_herbs_task for user {user_id}: {e}")
            await state.clear()

    task = asyncio.create_task(gather_herbs_task())
    active_hunts[user_id] = task

load_items()
load_data()
print(f"Locations in get_location: {app.locations.locations}")