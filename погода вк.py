import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import requests
import time
from datetime import datetime, timedelta
import re
import logging
import sys

# --- КОНФИГУРАЦИЯ ---
VK_TOKEN = "vk1.a.tIrqY-2oTKYnFVzEiivnRf-7ayAM3eNrewM8YqUt1etBwOLOvWul3J27Fj7ysb3ujFJgwifqebxzWJRoszlf0txWJtQO55CKpTUGT49C3iOYcJ6itqhtjuUeuQn1GbFVVRPvGNMouuvbrhGQrYYAP_gZtFwqf-Q4a51C01TE8IhGLTxrrYMrcDl9PAiPW14rz02gwRnunRwEDCi29eV65w"
WEATHER_TOKEN = "830c59b19e3968c7636dad1512feefb8"
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

user_states = {}
processed_messages = {}  # {message_id: timestamp}
user_cooldowns = {}  # {user_id: last_message_time}

RUSSIAN_CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград",
    "Краснодар", "Саратов", "Тюмень", "Тольятти", "Ижевск",
    "Барнаул", "Ульяновск", "Иркутск", "Хабаровск", "Ярославль",
    "Владивосток", "Махачкала", "Томск", "Оренбург", "Кемерово",
    "Новокузнецк", "Рязань", "Астрахань", "Набережные Челны", "Пенза",
    "Липецк", "Киров", "Тула", "Чебоксары", "Калининград",
    "Курган", "Брянск", "Иваново", "Магнитогорск", "Тверь",
    "Ставрополь", "Нижний Тагил", "Белгород", "Архангельск", "Владимир",
    "Сочи", "Сургут", "Калуга", "Чита", "Орёл",
    "Смоленск", "Курск", "Волжский", "Череповец", "Вологда",
    "Саранск", "Якутск", "Мурманск", "Петрозаводск", "Грозный",
    "Кострома", "Таганрог", "Комсомольск-на-Амуре", "Йошкар-Ола", "Нальчик",
    "Благовещенск", "Шахты", "Дзержинск", "Стерлитамак", "Нижневартовск",
    "Новороссийск", "Химки", "Нижнекамск", "Старый Оскол", "Армавир",
    "Прокопьевск", "Бийск", "Братск", "Дербент", "Абакан",
    "Сыктывкар", "Ангарск", "Электросталь", "Каменск-Уральский", "Первоуральск",
    "Альметьевск", "Рубцовск", "Копейск", "Одинцово", "Пятигорск",
    "Новочеркасск", "Златоуст", "Миасс", "Сызрань", "Люберцы"
]

WORLD_CITIES = [
    "London", "Paris", "Berlin", "Rome", "Madrid",
    "Barcelona", "Amsterdam", "Vienna", "Prague", "Budapest",
    "Warsaw", "Stockholm", "Oslo", "Helsinki", "Copenhagen",
    "Dublin", "Lisbon", "Athens", "Istanbul", "Moscow",
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Tokyo", "Osaka", "Kyoto", "Seoul", "Busan",
    "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hong Kong",
    "Singapore", "Bangkok", "Dubai", "Mumbai", "Delhi",
    "Sydney", "Melbourne", "Toronto", "Vancouver", "Montreal"
]

ALL_CITIES = RUSSIAN_CITIES + WORLD_CITIES

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session, wait=25)

# Получаем ID бота
bot_id = None
try:
    bot_info = vk.groups.getById()
    bot_id = bot_info[0]['id']
    print(f"ID бота: {bot_id}")
except:
    print("Не удалось получить ID бота")


def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button('Узнать погоду', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Прогноз на дату', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Выбрать город', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Помощь', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def get_city_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=True)
    for i, city in enumerate(ALL_CITIES[:8]):
        keyboard.add_button(city, color=VkKeyboardColor.SECONDARY)
        if (i + 1) % 4 == 0:
            keyboard.add_line()
    keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button('Ввести вручную', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


def get_back_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=True)
    keyboard.add_button('В главное меню', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def get_weather(city_name):
    params = {'q': city_name, 'appid': WEATHER_TOKEN, 'units': 'metric', 'lang': 'ru'}
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=10)
        data = response.json()
        if response.status_code == 200:
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            wind = data['wind']['speed']
            pressure = data['main']['pressure']
            return {
                'success': True,
                'message': (f"Погода в городе {city_name.capitalize()}\n\n"
                            f"Температура: {temp}C (ощущается как {feels_like}C)\n"
                            f"Описание: {description.capitalize()}\n"
                            f"Влажность: {humidity}%\n"
                            f"Ветер: {wind} м/с\n"
                            f"Давление: {pressure} гПа"),
                'city': city_name
            }
        else:
            if data.get('message') == 'city not found':
                return {'success': False, 'message': f"Город '{city_name}' не найден."}
            return {'success': False, 'message': "Ошибка API погоды."}
    except Exception as e:
        return {'success': False, 'message': f"Ошибка: {str(e)}"}


def get_forecast(city_name, date_str=None):
    params = {'q': city_name, 'appid': WEATHER_TOKEN, 'units': 'metric', 'lang': 'ru', 'cnt': 40}
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        data = response.json()
        if response.status_code == 200:
            if date_str:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                forecast_list = data['list']
                day_forecasts = [f for f in forecast_list if datetime.fromtimestamp(f['dt']).date() == target_date]
                if day_forecasts:
                    temps = [f['main']['temp'] for f in day_forecasts]
                    min_temp = min(temps)
                    max_temp = max(temps)
                    description = day_forecasts[len(day_forecasts) // 2]['weather'][0]['description']
                    return {
                        'success': True,
                        'message': (f"Прогноз на {date_str}\n\n"
                                    f"Мин: {min_temp}C | Макс: {max_temp}C\n"
                                    f"{description.capitalize()}"),
                        'city': city_name
                    }
                else:
                    return {'success': False, 'message': "Прогноз на эту дату недоступен."}
            else:
                forecast_list = data['list'][:24]
                message = f"Прогноз на 3 дня для {city_name}\n\n"
                current_date = None
                for forecast in forecast_list:
                    forecast_date = datetime.fromtimestamp(forecast['dt']).strftime('%d.%m')
                    if forecast_date != current_date:
                        current_date = forecast_date
                        message += f"\n{forecast_date}:\n"
                    temp = forecast['main']['temp']
                    desc = forecast['weather'][0]['description']
                    message += f"  - {temp}C - {desc}\n"
                return {'success': True, 'message': message, 'city': city_name}
        else:
            return {'success': False, 'message': "Ошибка получения прогноза."}
    except Exception as e:
        return {'success': False, 'message': f"Ошибка: {str(e)}"}


def handle_start(user_id):
    message = "Привет! Я бот погоды.\n\nВыберите действие в меню!"
    send_message(user_id, message, get_main_keyboard())
    user_states[user_id] = {'state': 'main'}


def handle_help(user_id):
    message = "Помощь\n\nИспользуйте кнопки меню или команды:\n/start, /help, /city, /data"
    send_message(user_id, message, get_back_keyboard())


def handle_city(user_id):
    message = "Выберите город:"
    send_message(user_id, message, get_city_keyboard())
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]['state'] = 'city_selection'


def handle_data(user_id):
    if user_id not in user_states or 'city' not in user_states[user_id]:
        send_message(user_id, "Сначала выберите город!", get_main_keyboard())
        return
    message = "Введите дату (ГГГГ-ММ-ДД) или напишите 'завтра':"
    send_message(user_id, message, get_back_keyboard())
    user_states[user_id]['state'] = 'date_selection'


def send_message(user_id, message, keyboard=None):
    try:
        vk.messages.send(user_id=user_id, message=message, random_id=get_random_id(), keyboard=keyboard)
        time.sleep(0.3)
    except Exception as e:
        print(f"Ошибка отправки: {e}")


def clean_vk_text(text):
    if not text:
        return ""
    cleaned = re.sub(r'[✓✔✅]', '', text).strip()
    return cleaned


def is_message_duplicate(message_id):
    """Проверяет, обрабатывали ли уже это сообщение"""
    if not message_id:
        return False

    current_time = time.time()

    if message_id in processed_messages:
        return True

    processed_messages[message_id] = current_time

    # Чистим старые записи (старше 10 секунд)
    keys_to_delete = [mid for mid, timestamp in processed_messages.items()
                      if current_time - timestamp > 10]
    for key in keys_to_delete:
        del processed_messages[key]

    return False


def is_user_on_cooldown(user_id):
    """Проверяет, не слишком ли быстро пользователь отправляет сообщения"""
    current_time = time.time()

    if user_id in user_cooldowns:
        last_time = user_cooldowns[user_id]
        if current_time - last_time < 1:  # Минимум 1 секунда между сообщениями
            return True

    user_cooldowns[user_id] = current_time
    return False


print("Бот запущен...")

for event in longpoll.listen():
    try:
        if event.type == VkEventType.MESSAGE_NEW:
            # Проверяем, что это входящее сообщение от пользователя (не от бота)
            if event.from_user and not event.from_me:
                user_id = event.user_id
                message_id = getattr(event, 'message_id', None)
                raw_text = event.text

                # Проверяем на дубли
                if is_message_duplicate(message_id):
                    print(f"Пропущен дубль сообщения {message_id}")
                    continue

                # Проверяем cooldown
                if is_user_on_cooldown(user_id):
                    print(f"Пользователь {user_id} на cooldown")
                    continue

                # Очищаем текст
                message_text = clean_vk_text(raw_text) if raw_text else ""

                if not message_text:
                    continue

                print(f"Обработка сообщения от {user_id}: '{message_text}'")

                if user_id not in user_states:
                    user_states[user_id] = {'state': 'main'}

                current_state = user_states[user_id].get('state', 'main')
                text_lower = message_text.lower()

                # Обработка команд
                if text_lower in ['/start', 'запуск', 'старт']:
                    handle_start(user_id)

                elif text_lower in ['/help', 'помощь', 'help']:
                    handle_help(user_id)

                elif text_lower in ['/city', 'город', 'city'] or message_text == 'Выбрать город':
                    handle_city(user_id)

                elif text_lower in ['/data', 'дата', 'data'] or message_text == 'Прогноз на дату':
                    handle_data(user_id)

                elif message_text == 'Узнать погоду':
                    if 'city' in user_states[user_id]:
                        result = get_weather(user_states[user_id]['city'])
                        send_message(user_id, result['message'], get_main_keyboard())
                    else:
                        send_message(user_id, "Выберите город сначала!", get_city_keyboard())

                elif message_text == 'Помощь':
                    handle_help(user_id)

                elif message_text in ['Назад', 'В главное меню']:
                    handle_start(user_id)

                elif message_text == 'Ввести вручную':
                    send_message(user_id, "Введите название города:", get_back_keyboard())
                    user_states[user_id]['state'] = 'manual_city_input'

                elif text_lower == 'завтра':
                    if 'city' in user_states[user_id]:
                        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                        result = get_forecast(user_states[user_id]['city'], tomorrow)
                        send_message(user_id, result['message'], get_main_keyboard())
                    else:
                        send_message(user_id, "Выберите город сначала!", get_city_keyboard())

                elif current_state == 'manual_city_input':
                    result = get_weather(message_text)
                    if result['success']:
                        user_states[user_id]['city'] = message_text
                        send_message(user_id, result['message'], get_main_keyboard())
                        user_states[user_id]['state'] = 'main'
                    else:
                        send_message(user_id, result['message'] + "\nПопробуйте еще раз:", get_back_keyboard())

                elif current_state == 'city_selection':
                    if message_text in ALL_CITIES:
                        result = get_weather(message_text)
                        if result['success']:
                            user_states[user_id]['city'] = message_text
                            send_message(user_id, result['message'], get_main_keyboard())
                            user_states[user_id]['state'] = 'main'
                        else:
                            send_message(user_id, result['message'], get_city_keyboard())
                    elif message_text not in ['Назад', 'Ввести вручную']:
                        send_message(user_id, "Пожалуйста, выберите город из списка или нажмите 'Ввести вручную'",
                                     get_city_keyboard())

                elif current_state == 'date_selection':
                    if 'city' not in user_states[user_id]:
                        send_message(user_id, "Выберите город!", get_city_keyboard())
                        continue

                    date_str = message_text.strip()
                    try:
                        if text_lower == 'завтра':
                            date_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                        else:
                            datetime.strptime(date_str, '%Y-%m-%d')

                        result = get_forecast(user_states[user_id]['city'], date_str)
                        send_message(user_id, result['message'], get_main_keyboard())
                        user_states[user_id]['state'] = 'main'
                    except ValueError:
                        send_message(user_id, "Неверный формат даты (ГГГГ-ММ-ДД)", get_back_keyboard())

                elif text_lower.startswith('погода '):
                    city = message_text[7:].strip()
                    if city:
                        result = get_weather(city)
                        if result['success']:
                            user_states[user_id]['city'] = city
                        send_message(user_id, result['message'], get_main_keyboard())
                    else:
                        send_message(user_id, "Пример: погода Москва", get_main_keyboard())

                elif current_state == 'main' and message_text:
                    send_message(user_id, "Не понял команду. Нажмите /help или используйте меню", get_main_keyboard())

    except KeyboardInterrupt:
        print("\nОстановка бота...")
        break
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback

        traceback.print_exc()
        continue
# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'  # Перезаписывать файл при каждом запуске
)

logging.info("=== ЗАПУСК БОТА ===")


