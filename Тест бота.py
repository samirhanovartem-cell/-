#  ИМПОРТ СТАНДАРТНЫХ И СТОРОННИХ БИБЛИОТЕК

import telebot          # Основная библиотека для создания Telegram-ботов (pyTelegramBotAPI)
import requests         # Отправка HTTP-запросов к внешним API (OpenWeatherMap)
import time             # Работа со временем (паузы, таймауты)
from datetime import datetime, timedelta  # Обработка дат и времени
import sqlite3          # Встроенная библиотека для работы с локальной БД SQLite

#  НАСТРОЙКА API-КЛЮЧЕЙ 

# Токен Telegram-бота, полученный у @BotFather в Telegram
TELEGRAM_TOKEN = "8408071612:AAGLGXap5PITGGFxCS9ilLadCzr5HBNxX0M"

# API-ключ от сервиса OpenWeatherMap 
OPENWEATHER_API_KEY = "830c59b19e3968c7636dad1512feefb8"

# Создание экземпляра бота с передачей токена для аутентификации в Telegram
bot = telebot.TeleBot(TELEGRAM_TOKEN)

#  СПИСОК ДОСТУПНЫХ ГОРОДОВ ДЛЯ ВЫБОРА

# Содержит 100+ городов: крупные города России + мировые мегаполисы
# Используется для формирования кнопок и валидации ввода пользователя
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

#  ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ SQLITE

# Создание/открытие файла базы данных 'users.db' в текущей директории
# Параметр check_same_thread=False разрешает использование соединения 
# в однопоточном режиме бота (безопасно для telebot)
conn = sqlite3.connect('users.db', check_same_thread=False)

# Создание курсора — объекта для выполнения SQL-запросов
cursor = conn.cursor()

# Создание таблицы 'users', если она ещё не существует
# Структура таблицы:
#   • chat_id (INTEGER, PRIMARY KEY) — уникальный ID чата в Telegram
#   • city (TEXT, NOT NULL) — название города, выбранного пользователем
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        city TEXT NOT NULL
    )
''')

# Фиксация изменений в базе данных (сохранение структуры таблицы на диск)
conn.commit()

#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ

def save_user_city(chat_id, city):
    """
    Сохраняет или обновляет город пользователя в базе данных.
    
    Параметры:
        chat_id (int): Уникальный идентификатор чата пользователя в Telegram
        city (str): Название города для сохранения
    
    Особенности:
        • Использует INSERT OR REPLACE — если запись существует, она обновляется
        • Параметризованный запрос (?, ?) защищает от SQL-инъекций
        • Автоматическая фиксация изменений через conn.commit()
    """
    cursor.execute('INSERT OR REPLACE INTO users (chat_id, city) VALUES (?, ?)', (chat_id, city))
    conn.commit()


def get_user_city(chat_id):
    """
    Получает сохранённый город пользователя из базы данных.
    
    Параметры:
        chat_id (int): Уникальный идентификатор чата пользователя в Telegram
    
    Возвращает:
        str или None: Название города, если запись найдена, иначе None
    
    Логика:
        • Выполняет SELECT-запрос с фильтрацией по chat_id
        • fetchone() возвращает первую строку результата или None
        • result[0] извлекает значение из первого столбца (city)
    """
    cursor.execute('SELECT city FROM users WHERE chat_id = ?', (chat_id,))
    result = cursor.fetchone()
    return result[0] if result else None

#  ОБРАБОТЧИК КОМАНДЫ /start — ПРИВЕТСТВИЕ ПОЛЬЗОВАТЕЛЯ

@bot.message_handler(commands=['start'])
def start(message):
    """
    Обрабатывает команду /start.
    Показывает персонализированное приветствие с учётом сохранённого города.
    """
    chat_id = message.chat.id          # Уникальный ID чата пользователя
    city = get_user_city(chat_id)      # Попытка получить сохранённый город из БД
    
    if city:
        # Приветствие для возвратившегося пользователя с сохранённым городом
        bot.send_message(
            chat_id,
            f"🌤 Добро пожаловать обратно! Ваш город: {city}\n"
            "Нажмите /data — выбрать день (прогноз на 4 дня).\n"
            "Или /city — сменить город."
        )
    else:
        # Приветствие для нового пользователя
        bot.send_message(
            chat_id,
            "🌤 Привет! Я бот погоды.\n"
            "1. Нажмите /city и выберите город.\n"
            "2. Нажмите /data — выбрать день (прогноз на 4 дня)."
        )

#  ОБРАБОТЧИК КОМАНДЫ /help — СПРАВКА ПО ИСПОЛЬЗОВАНИЮ

@bot.message_handler(commands=['help'])
def help_cmd(message):
    """
    Обрабатывает команду /help.
    Отправляет пользователю инструкцию по использованию бота.
    """
    bot.send_message(
        message.chat.id,
        "🛠 Как пользоваться:\n"
        "- /city — выбрать город из списка\n"
        "- /data — выбрать день недели (сегодня + 3 дня)\n"
        "- Бот покажет погоду на выбранный день."
    )

#  ОБРАБОТЧИК КОМАНДЫ /city — ВЫБОР ГОРОДА

@bot.message_handler(commands=['city'])
def city_cmd(message):
    """
    Обрабатывает команду /city.
    Отображает клавиатуру с выбором города из списка CITIES.
    """
    # Создание интерактивной клавиатуры под полем ввода
    #   • resize_keyboard=True — компактный размер клавиатуры
    #   • one_time_keyboard=True — клавиатура скроется после выбора
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    
    # Добавление кнопок со всеми городами из списка CITIES
    for city in CITIES:
        markup.add(city)  # Каждый город становится отдельной кнопкой
    
    # Отправка сообщения с прикреплённой клавиатурой
    bot.send_message(message.chat.id, "Выберите город:", reply_markup=markup)

#  ОБРАБОТЧИК КОМАНДЫ /data — ВЫБОР ДАТЫ

@bot.message_handler(commands=['data'])
def data_cmd(message):
    """
    Обрабатывает команду /data.
    Отображает клавиатуру с выбором дня (сегодня + 3 дня).
    Перед показом проверяет, выбран ли город пользователем.
    """
    chat_id = message.chat.id
    city = get_user_city(chat_id)  # Получение сохранённого города из БД
    
    # Проверка: город должен быть выбран до запроса прогноза
    if not city:
        bot.send_message(chat_id, "❌ Сначала выберите город через /city.")
        return  # Прерывание выполнения функции
    
    # Расчёт списка из 4 дат: сегодня, завтра, послезавтра, через 3 дня
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(4)]
    
    # Создание клавиатуры для выбора даты
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for d in dates:
        # Получение короткого названия дня недели (Пн, Вт, Ср...)
        day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][d.weekday()]
        # Форматирование кнопки: "Пн 24.11"
        btn_text = f"{day_name} {d.strftime('%d.%m')}"
        markup.add(btn_text)
    
    # Отправка клавиатуры с выбором дня
    bot.send_message(chat_id, "Выберите день:", reply_markup=markup)

#  УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    """
    Обрабатывает ЛЮБОЕ текстовое сообщение от пользователя.
    Выполняется после специфичных обработчиков (/start, /city, /data).
    Логика:
        1. Если сообщение — название города из списка → сохранить в БД
        2. Если сообщение — дата в формате "Пн 24.11" → показать прогноз
        3. Иначе — показать подсказку
    """
    chat_id = message.chat.id
    text = message.text.strip()  # Удаление пробелов по краям текста
    
    #  Пользователь выбрал город из списка
    if text in CITIES:
        save_user_city(chat_id, text)  # Сохранение города в БД
        bot.send_message(chat_id, f"✅ Город сохранён: {text}. Теперь нажмите /data.")
        return  # Прерывание дальнейшей обработки
    
    #  Пользователь выбрал дату (формат: "Пн 24.11")
    if any(text.startswith(d) for d in ["Пн ", "Вт ", "Ср ", "Чт ", "Пт ", "Сб ", "Вс "]):
        city = get_user_city(chat_id)  # Получение сохранённого города
        
        # Двойная проверка: город должен быть выбран
        if not city:
            bot.send_message(chat_id, "❌ Сначала выберите город через /city.")
            return
        
        try:
            # Извлечение части с датой ("24.11") из текста кнопки ("Пн 24.11")
            date_str = text.split()[1]
            # Разделение на день и месяц, преобразование в числа
            day, month = map(int, date_str.split('.'))
            
            # Сборка полной даты с текущим годом
            today = datetime.now().date()
            year = today.year
            target_date = datetime(year, month, day).date()
            
            # Коррекция года для случаев перехода через Новый год
            # (например: сегодня 2 января, пользователь выбрал "31.12")
            if target_date < today and (today - target_date).days > 300:
                target_date = datetime(year + 1, month, day).date()
            
            # Проверка: дата должна быть в диапазоне сегодня + 3 дня
            valid_dates = [today + timedelta(days=i) for i in range(4)]
            if target_date not in valid_dates:
                bot.send_message(chat_id, "❌ Эта дата вне диапазона. Используйте кнопки.")
                return
            
            # Получение и отображение прогноза погоды
            get_weather(bot, chat_id, city, target_date)
        
        except Exception as e:
            # Обработка ошибок парсинга даты
            bot.send_message(chat_id, "❌ Не удалось распознать дату. Используйте кнопки.")
        return
    
    #  Неизвестное сообщение — показ подсказки
    bot.send_message(
        chat_id,
        "Пожалуйста, используйте:\n"
        "/city — выбрать город\n"
        "/data — выбрать день"
    )

#  ФУНКЦИЯ ПОЛУЧЕНИЯ И ОТОБРАЖЕНИЯ ПРОГНОЗА ПОГОДЫ

def get_weather(bot, chat_id, city, date):
    """
    Получает прогноз погоды с OpenWeatherMap API и отправляет его пользователю.
    
    Параметры:
        bot (TeleBot): Экземпляр бота для отправки сообщений
        chat_id (int): ID чата пользователя
        city (str): Название города для запроса
        date (date): Дата прогноза (объект datetime.date)
    
    Логика:
        1. Отправка запроса к API OpenWeatherMap (прогноз на 5 дней)
        2. Поиск прогноза, ближайшего к 12:00 указанной даты
        3. Форматирование и отправка сообщения с погодой
    """
    # URL эндпоинта API для прогноза на 5 дней (данные с шагом 3 часа)
    url = "http://api.openweathermap.org/data/2.5/forecast"
    
    # Параметры запроса к API
    params = {
        'q': city,               # Название города
        'appid': OPENWEATHER_API_KEY,  # API-ключ для аутентификации
        'units': 'metric',       # Единицы измерения: градусы Цельсия
        'lang': 'ru'             # Язык описания погоды: русский
    }
    
    try:
        # Отправка GET-запроса к API с таймаутом 10 секунд
        resp = requests.get(url, params=params, timeout=10)
        
        # Проверка статуса ответа 
        if resp.status_code != 200:
            # Извлечение сообщения об ошибке из JSON-ответа API
            error_msg = resp.json().get('message', 'Unknown error')
            bot.send_message(chat_id, f"❌ Ошибка OpenWeather: {error_msg}")
            return
        
        # Парсинг JSON-ответа в Python-словарь
        data = resp.json()
        
        # Поиск прогноза, ближайшего к полудню (12:00) указанной даты
        best = None      # Лучший найденный прогноз
        min_diff = 999   # Минимальная разница в часах до 12:00
        
        for item in data['list']:
            # Преобразование timestamp в объект datetime
            dt = datetime.fromtimestamp(item['dt'])
            
            # Проверка: прогноз относится к запрошенной дате
            if dt.date() == date:
                # Расчёт разницы между часом прогноза и 12:00
                diff = abs(dt.hour - 12)
                # Выбор прогноза с минимальной разницей
                if diff < min_diff:
                    min_diff = diff
                    best = item
        
        # Проверка: найден ли подходящий прогноз
        if not best:
            bot.send_message(chat_id, "🌤 Прогноз на этот день не найден.")
            return
        
        # Извлечение параметров погоды из структуры JSON
        temp = best['main']['temp']                      # Температура (°C)
        desc = best['weather'][0]['description'].capitalize()  # Описание (с заглавной буквы)
        hum = best['main']['humidity']                   # Влажность (%)
        wind = best['wind']['speed']                     # Скорость ветра (м/с)
        
        # Получение полного названия дня недели для красивого вывода
        weekday_names = ["понедельник", "вторник", "среда", "четверг", 
                         "пятница", "суббота", "воскресенье"]
        weekday = weekday_names[date.weekday()]
        
        # Формирование итогового сообщения с эмодзи для лучшей читаемости
        msg = (
            f"🌤 Погода в {city} на {weekday}, {date.strftime('%d.%m')}:\n"
            f"🌡 {temp:.1f}°C\n"          # Форматирование: 1 знак после запятой
            f"☁️ {desc}\n"
            f"💧 Влажность: {hum}%\n"
            f"💨 Ветер: {wind} м/с"
        )
        
        # Отправка сообщения пользователю
        bot.send_message(chat_id, msg)
    
    except Exception as e:
        # Перехват любых исключений (сетевые ошибки, проблемы с парсингом)
        bot.send_message(chat_id, f"⚠️ Ошибка при получении погоды: {str(e)}")

def generate_recommendation(temp, description, humidity, wind_speed):
    """
    Генерирует рекомендацию на основе погодных условий.
    """
    desc = description.lower()
    advice = []

    # Рекомендации по осадкам
    if "дождь" in desc or "ливень" in desc or "моросящий" in desc:
        advice.append("🌧 Возьмите зонт и непромокаемую одежду.")
    elif "снег" in desc:
        advice.append("❄️ Одевайтесь потеплее и будьте осторожны на дорогах.")
    elif "облачно" in desc:
        advice.append("☁️ Пасмурно — не забудьте про хорошее настроение!")
    elif "ясно" in desc or "солнечно" in desc:
        advice.append("☀️ Отличная погода для прогулки! Не забудьте солнцезащитные очки.")

    # Рекомендации по температуре
    if temp < -10:
        advice.append("🥶 Очень холодно! Наденьте термобельё, шапку и перчатки.")
    elif temp < 0:
        advice.append("🧊 На улице мороз — одевайтесь тепло.")
    elif 0 <= temp < 10:
        advice.append("🧥 Прохладно — возьмите куртку.")
    elif 10 <= temp < 20:
        advice.append("👕 Комфортная температура — можно гулять в лёгкой одежде.")
    elif 20 <= temp < 28:
        advice.append("😎 Приятно тепло — отличный день для парка или кофе на свежем воздухе.")
    elif temp >= 28:
        advice.append("🔥 Жарко! Пейте больше воды и избегайте прямого солнца в полдень.")

    # Ветер
    if wind_speed > 10:
        advice.append("💨 Сильный ветер — придерживайтесь укрытий и закрепите головной убор.")

    # Высокая влажность + жара
    if temp >= 25 and humidity > 70:
        advice.append("💦 Высокая влажность — может быть душно. Избегайте перегрева.")

    # Если нет конкретных советов — дадим общий
    if not advice:
        advice.append("🌤 Хорошей погоды вам!")

    return "\n".join(advice)

#  ЗАПУСК БОТА 

if __name__ == '__main__':
    """
    Основной блок выполнения программы.
    Выполняется только при прямом запуске скрипта
    """
    print(" Удаляем webhook и запускаем бота...")
    
    # Отключение режима вебхуков 
    bot.remove_webhook()
    
    # Пауза 1 секунда для применения изменений на стороне Telegram
    time.sleep(1)
    
    try:
        # Запуск бота в режиме долгого опроса (long polling)
        #   • none_stop=True — продолжать работу при возникновении ошибок
        #   • timeout=30 — таймаут одного запроса к серверам Telegram
        bot.polling(none_stop=True, timeout=30)
    
    except KeyboardInterrupt:
        # Обработка остановки через Ctrl+C
        print("\n Остановка бота...")
        conn.close()  # Корректное закрытие соединения с БД
        print(" Соединение с БД закрыто")
    
    except Exception as e:
        # Обработка любых критических ошибок
        print(f" Критическая ошибка: {e}")
        conn.close()  # Гарантированное закрытие БД даже при падении
        print(" Соединение с БД закрыто (аварийное завершение)")

