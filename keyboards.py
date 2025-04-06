from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import(ReplyKeyboardBuilder, InlineKeyboardBuilder)
from app.locations import locations  # Импорт из locations.py
import logging
logger = logging.getLogger(__name__)



'''
main = ReplyKeyboardMarkup(keyboard = [\
    [KeyboardButton(text = 'Профиль')],\
    [KeyboardButton(text = 'Локация'), KeyboardButton(text = 'Переходы'),]\
],\
resize_keyboard = True, input_field_placeholder='Выберите пункт меню'

)
'''
'''
main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Переходы', callback_data='roads')],
    [InlineKeyboardButton(text='Локация', callback_data='location'),
     InlineKeyboardButton(text='Осмотреться', callback_data='lookout')]
])
'''

settings = InlineKeyboardMarkup(inline_keyboard =[\
[InlineKeyboardButton(text='Осмотреться', url = 'https://vscodethemes.com/')]])

locs =['Мшистая норка', 'Цветочная тропинка', 'Сияющий пруд']

async def inline_locs():
    keyboard = InlineKeyboardBuilder()
    for loc in locs:
        keyboard.add(InlineKeyboardButton(text=loc, url = 'https://vscodethemes.com/'))
    return keyboard.adjust(2).as_markup()

async def choose_sex():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text = "Кот", callback_data="sex_male"),
            InlineKeyboardButton(text = "Кошка", callback_data="sex_female")
        ]
    ])
    return keyboard

async def choose_sex():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text = "Кот", callback_data="sex_male"),
            InlineKeyboardButton(text = "Кошка", callback_data="sex_female")
        ]
    ])
    return keyboard

async def choose_clan():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text = "Красный", callback_data="clan1"),
            InlineKeyboardButton(text = "Синий", callback_data="clan2")
        ], \
        [
            InlineKeyboardButton(text = "Желтый", callback_data="clan3"),
            InlineKeyboardButton(text = "Зеленый", callback_data="clan4")
        ]
    ])
    return keyboard

async def loc_1_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Осмотреться", callback_data="look_around"),
            InlineKeyboardButton(text="Охота", callback_data="start_hunt")
        ]
    ])
    return keyboard

async def location_buttons(current_location_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Осмотреться", callback_data="look_around"))
    keyboard.add(InlineKeyboardButton(text="Переходы", callback_data="roads"))
    keyboard.add(InlineKeyboardButton(text="Профиль", callback_data="show_profile"))
    keyboard.add(InlineKeyboardButton(text="Действия", callback_data="show_actions"))
    return keyboard.adjust(2).as_markup()

async def action_buttons(current_location_id):
    """
    Создает клавиатуру с доступными действиями для текущей локации.
    """
    logger.info(f"Формируем действия для локации ID: {current_location_id}, тип: {type(current_location_id)}")
    keyboard = InlineKeyboardBuilder()
    
    # Приводим к int на случай, если передали строку
    try:
        location_id = int(current_location_id)
    except (ValueError, TypeError):
        logger.error(f"Некорректный ID локации: {current_location_id}, используем дефолт 1")
        location_id = 1
    
    if location_id == 1:  # "Цветочная тропа"
        keyboard.add(InlineKeyboardButton(text="Охота", callback_data="start_hunt"))
        keyboard.add(InlineKeyboardButton(text="Собрать травы", callback_data="start_gather_herbs"))
        logger.info("Добавлены кнопки 'Охота' и 'Собрать травы'")
    else:
        logger.info(f"Действия не добавлены, локация ID {location_id} не 'Цветочная тропа'")
    
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back_to_location"))
    markup = keyboard.adjust(2).as_markup()
    logger.info(f"Готовая клавиатура: {markup.inline_keyboard}")
    return markup

async def transition_buttons(current_location_id):
    keyboard = InlineKeyboardBuilder()
    for adjacent_id in locations[current_location_id]['adjacent']:
        adjacent_name = locations[adjacent_id]['name']
        keyboard.add(InlineKeyboardButton(text=adjacent_name, callback_data=f"move_to_{adjacent_id}"))
    return keyboard.adjust(2).as_markup()

async def cancel_button():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Отменить", callback_data="cancel_button"))
    return keyboard.as_markup()

async def profile_buttons(current_location_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Инвентарь", callback_data="show_inventory"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back_to_location"))
    return keyboard.adjust(1).as_markup()