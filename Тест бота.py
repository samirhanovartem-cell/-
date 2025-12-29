import telebot
import requests
import time
from datetime import datetime, timedelta


TELEGRAM_TOKEN = "8408071612:AAGLGXap5PITGGFxCS9ilLadCzr5HBNxX0M"
OPENWEATHER_API_KEY = "830c59b19e3968c7636dad1512feefb8"

bot = telebot.TeleBot(TELEGRAM_TOKEN)


CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград",
    "Краснодар", "Саратов", "Тюмень", "Тольятти", "Ижевск",
    "Барнаул", "Ульяновск", "Иркутск", "Хабаровск", "Ярославль",
    "Владивосток", "Махачкала", "Томск", "Оренбург", "Кемерово",
    "Новокузнецк", "Рязань", "Астрахань", "Набережные Челны", "Пенза",
    "Липецк", "Киров", "Чебоксары", "Тула", "Калининград",
    "Курск", "Улан-Удэ", "Ставрополь", "Сочи", "Тверь",
    "Магнитогорск", "Иваново", "Брянск", "Сургут", "Белгород",
    "Архангельск", "Владимир", "Курган", "Смоленск", "Калуга",
    "Чита", "Саранск", "Кострома", "Вологда", "Петрозаводск",
    "Нью-Йорк", "Лос-Анджелес", "Чикаго", "Лондон", "Париж",
    "Берлин", "Рим", "Мадрид", "Токио", "Пекин",
    "Шанхай", "Сеул", "Дели", "Мумбаи", "Сан-Паулу",
    "Буэнос-Айрес", "Каир", "Мехико", "Стамбул", "Дубай",
    "Сидней", "Торонто", "Ванкувер", "Амстердам", "Вена",
    "Цюрих", "Стокгольм", "Хельсинки", "Осло", "Копенгаген",
    "Брюссель", "Прага", "Варшава", "Будапешт", "Афины",
    "Лиссабон", "Дублин", "Рейкьявик", "Кейптаун"
]

# Хранилище: {chat_id: {"city": "Москва"}}
user_data = {}


# --- Команды ---
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = user_data.get(chat_id, {})
    bot.send_message(
        chat_id,
        "🌤 Привет! Я бот погоды.\n"
        "1. Нажмите /city и выберите город.\n"
        "2. Нажмите /data — выберите день (прогноз на 4 дня)."
    )


@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.send_message(
        message.chat.id,
        "🛠 Как пользоваться:\n"
        "- /city — выбрать город из списка (включая Курган)\n"
        "- /data — выбрать день недели (сегодня + 3 дня)\n"
        "- Бот покажет погоду на выбранный день."
    )


@bot.message_handler(commands=['city'])
def city_cmd(message):
    chat_id = message.chat.id
    user_data[chat_id] = user_data.get(chat_id, {})

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for city in CITIES:
        markup.add(city)
    bot.send_message(chat_id, "Выберите город:", reply_markup=markup)


@bot.message_handler(commands=['data'])
def data_cmd(message):
    chat_id = message.chat.id
    if chat_id not in user_data or not user_data[chat_id].get('city'):
        bot.send_message(chat_id, "❌ Сначала выберите город через /city.")
        return

    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(4)]

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for d in dates:
        day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][d.weekday()]
        btn_text = f"{day_name} {d.strftime('%d.%m')}"
        markup.add(btn_text)
    bot.send_message(chat_id, "Выберите день:", reply_markup=markup)


# --- Обработка ввода ---
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # Если сообщение — это город из списка
    if text in CITIES:
        user_data[chat_id] = user_data.get(chat_id, {})
        user_data[chat_id]['city'] = text
        bot.send_message(chat_id, f"✅ Город установлен: {text}. Теперь нажмите /data.")
        return

    # Если сообщение — это дата в формате "Пн 24.11"
    if any(text.startswith(d) for d in ["Пн ", "Вт ", "Ср ", "Чт ", "Пт ", "Сб ", "Вс "]):
        if chat_id not in user_data or not user_data[chat_id].get('city'):
            bot.send_message(chat_id, "❌ Сначала выберите город через /city.")
            return

        try:
            date_str = text.split()[1]  # "24.11"
            day, month = map(int, date_str.split('.'))
            today = datetime.now().date()
            year = today.year
            target_date = datetime(year, month, day).date()

            # Коррекция для 1 января и т.п.
            if target_date < today and (today - target_date).days > 300:
                target_date = datetime(year + 1, month, day).date()

            # Проверка диапазона
            valid_dates = [today + timedelta(days=i) for i in range(4)]
            if target_date not in valid_dates:
                bot.send_message(chat_id, "❌ Эта дата вне диапазона. Используйте кнопки.")
                return

            city = user_data[chat_id]['city']
            get_weather(bot, chat_id, city, target_date)

        except Exception as e:
            bot.send_message(chat_id, "❌ Не удалось распознать дату. Используйте кнопки.")
        return

    # Любое другое сообщение
    bot.send_message(
        chat_id,
        "Пожалуйста, используйте:\n"
        "/city — выбрать город\n"
        "/data — выбрать день"
    )


# --- Получение погоды ---
def get_weather(bot, chat_id, city, date):
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': city,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric',
        'lang': 'ru'
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            error_msg = resp.json().get('message', 'Unknown error')
            bot.send_message(chat_id, f"❌ Ошибка OpenWeather: {error_msg}")
            return

        data = resp.json()
        best = None
        min_diff = 999
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            if dt.date() == date:
                diff = abs(dt.hour - 12)  # ближе к полудню
                if diff < min_diff:
                    min_diff = diff
                    best = item

        if not best:
            bot.send_message(chat_id, "🌤 Прогноз на этот день не найден.")
            return

        temp = best['main']['temp']
        desc = best['weather'][0]['description'].capitalize()
        hum = best['main']['humidity']
        wind = best['wind']['speed']

        weekday_names = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        weekday = weekday_names[date.weekday()]

        msg = (
            f"🌤 Погода в {city} на {weekday}, {date.strftime('%d.%m')}:\n"
            f"🌡 {temp:.1f}°C\n"
            f"☁️ {desc}\n"
            f"💧 Влажность: {hum}%\n"
            f"💨 Ветер: {wind} м/с"
        )
        bot.send_message(chat_id, msg)

    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Ошибка при получении погоды: {str(e)}")


if __name__ == '__main__':
    print("🚀 Удаляем webhook и запускаем бота...")
    bot.remove_webhook()
    time.sleep(1)
    try:
        bot.polling(none_stop=True, timeout=30)
    except Exception as e:

        print(f"🛑 Ошибка: {e}")
