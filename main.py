import telebot
import sqlite3
import os

bot = telebot.TeleBot('6948731078:AAGiZX4rO-S7DVK3-femTj2kG1oL3B3sqRY')

admin_ids = [1665454474, 1785007995]  # ID администраторов

# Путь к файлу базы данных
db_path = 'balances.db'

# Проверка существования базы данных и создание, если отсутствует
if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Создание таблицы balances с новыми полями
    cursor.execute('''
        CREATE TABLE balances (
            user_number INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            balance INTEGER
        )
    ''')

    conn.commit()
    conn.close()


# Функция для логирования
def log_action(action, admin_id, user_number, amount):
    print(f"Администратор с ID {admin_id} {action} участнику с номером {user_number} {amount} баллов.")


# Команда для проверки баланса
@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = message.chat.id
    conn = sqlite3.connect('balances.db')
    cursor = conn.cursor()

    cursor.execute('SELECT balance FROM balances WHERE user_id = ?', (user_id,))
    user_balance = cursor.fetchone()

    cursor.execute('SELECT user_number FROM balances WHERE user_id = ?', (user_id,))
    user_number = cursor.fetchone()

    if user_balance:
        bot.reply_to(message, f"Ваш баланс:\n🎉 {user_balance[0]} GeekCoin\nВаш номер: {str(user_number)[1:-2]}")
    else:
        bot.reply_to(message, f"Ваш баланс:\n❌ 0 GeekCoin\nВаш номер: {str(user_number)[1:-2]}")

    conn.close()


# Команда для получения максимального баланса участников
@bot.message_handler(commands=['leader'], func=lambda message: message.from_user.id in admin_ids)
def max_balance(message):
    conn = sqlite3.connect('balances.db')
    cursor = conn.cursor()

    cursor.execute('SELECT MAX(balance) FROM balances')
    max_balance = cursor.fetchone()[0]

    bot.reply_to(message, f"Максимальный баланс среди участников: {max_balance} GeekCoin")

    conn.close()


# Команда для проверки баланса участника администратором
@bot.message_handler(commands=['check_balance'], func=lambda message: message.from_user.id in admin_ids)
def check_user_balance(message):
    try:
        user_number = int(message.text.split()[1])
        conn = sqlite3.connect('balances.db')
        cursor = conn.cursor()

        cursor.execute('SELECT balance FROM balances WHERE user_number = ?', (user_number,))
        user_balance = cursor.fetchone()

        if user_balance:
            bot.reply_to(message, f"Баланс пользователя {user_number}:\n🎉 {user_balance[0]} GeekCoin")
        else:
            bot.reply_to(message, f"Пользователь с номером {user_number}:\n❌ 0 GeekCoin")

        conn.close()
    except (IndexError, ValueError):
        bot.reply_to(message, "Используйте команду в формате /check_balance user_number")


# Команда для начала работы с ботом
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    conn = sqlite3.connect('balances.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM balances WHERE user_id = ?', (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        cursor.execute('INSERT INTO balances (user_id, balance) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        cursor.execute('SELECT user_number FROM balances WHERE user_id = ?', (user_id,))
        user_number = cursor.fetchone()
        bot.reply_to(message,
                     f"👋 Добро пожаловать на GeekCon! \n\n📌 Ваш номер - {str(user_number)[1:-2]}, показывайте его волонтёрам на станциях, чтобы они могли начислить вам GeekCoin-ы\n\n📌 Чтобы узнать свой баланс, используйте /balance.\n\n 📌 Если хотите узнать все локации GeekCon используйте команду /events")
        print(f"Пользователь с ID {user_id} зарегистрировался")
    else:
        cursor.execute('SELECT user_number FROM balances WHERE user_id = ?', (user_id,))
        user_number = cursor.fetchone()
        print(f"Пользователь с ID {user_id} вернулся")
        bot.reply_to(message,
                     f"👋 Добро пожаловать обратно! Ваш номер - {str(user_number)[1:-2]}\n\n📌Чтобы узнать свой баланс, используйте /balance.")

    conn.close()


# Команда для добавления баланса администраторами
@bot.message_handler(commands=['add'], func=lambda message: message.from_user.id in admin_ids)
def add_balance(message):
    try:
        parts = message.text.split()
        admin_id = message.from_user.id
        user_number = int(parts[1])
        amount = int(parts[2])

        conn = sqlite3.connect('balances.db')
        cursor = conn.cursor()

        cursor.execute('SELECT balance FROM balances WHERE user_number = ?', (user_number,))
        user_balance = cursor.fetchone()

        if user_balance:
            new_balance = user_balance[0] + amount
            cursor.execute('UPDATE balances SET balance = ? WHERE user_number = ?', (new_balance, user_number))
            conn.commit()
            log_action("добавил", admin_id, user_number, amount)
            bot.reply_to(message, f"Баланс пользователя {user_number} увеличен на {amount}.")
            cursor.execute('SELECT user_id FROM balances WHERE user_number = ?', (user_number,))
            user_id = cursor.fetchone()
            bot.send_message(str(user_id)[1:-2], f"Вам начислено {amount} GeekCoin 🎉")

        else:
            bot.reply_to(message, f"Данный пользователь не найден.")

        conn.close()
    except (IndexError, ValueError):
        bot.reply_to(message, "Используйте команду в формате /add user_number amount")


# Команда для уменьшения баланса администраторами
@bot.message_handler(commands=['sub'], func=lambda message: message.from_user.id in admin_ids)
def subtract_balance(message):
    try:
        parts = message.text.split()
        admin_id = message.from_user.id
        user_number = int(parts[1])
        amount = int(parts[2])

        conn = sqlite3.connect('balances.db')
        cursor = conn.cursor()

        cursor.execute('SELECT balance FROM balances WHERE user_number = ?', (user_number,))
        user_balance = cursor.fetchone()

        if user_balance:
            if user_balance[0] >= amount:
                new_balance = user_balance[0] - amount
                cursor.execute('UPDATE balances SET balance = ? WHERE user_number = ?', (new_balance, user_number))
                conn.commit()
                log_action("уменьшил", admin_id, user_number, amount)
                bot.reply_to(message, f"Баланс пользователя {user_number} уменьшен на {amount}.")
                cursor.execute('SELECT user_id FROM balances WHERE user_number = ?', (user_number,))
                user_id = cursor.fetchone()
                bot.send_message(str(user_id)[1:-2], f"С вашего баланса отняли {amount} GeekCoin 😔")
            else:
                bot.reply_to(message, "Недостаточно средств на балансе пользователя.")

        else:
            bot.reply_to(message, f"Пользователь с номером {user_number} не найден.")

        conn.close()
    except (IndexError, ValueError):
        bot.reply_to(message, "Используйте команду в формате /sub user_number amount")


# Команда для получения событий на GeekCon
@bot.message_handler(commands=['events'])
def get_events(message):
    # Здесь можно добавить логику получения событий на текущий день или другую нужную информацию
    events_text = "Список событий на GeekCon сегодня:\n- Событие 1\n- Событие 2\n- Событие 3"

    bot.send_message(message.chat.id, events_text)


# Команда для вывода списка всех номеров с балансами
@bot.message_handler(commands=['all_balances'], func=lambda message: message.from_user.id in admin_ids)
def all_balances(message):
    conn = sqlite3.connect('balances.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_number, balance FROM balances')
    all_balances = cursor.fetchall()

    balances_text = "Список всех балансов:\n"
    for user_number, balance in all_balances:
        balances_text += f"Номер: {user_number}, Баланс: {balance} GeekCoin\n"

    bot.reply_to(message, balances_text)

    conn.close()


# Команда для удаления пользователя
@bot.message_handler(commands=['remove_user'], func=lambda message: message.from_user.id in admin_ids)
def remove_user(message):
    try:
        user_number = int(message.text.split()[1])
        conn = sqlite3.connect('balances.db')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM balances WHERE user_number = ?', (user_number,))
        conn.commit()

        bot.reply_to(message, f"Пользователь с номером {user_number} удален.")

        conn.close()
    except (IndexError, ValueError):
        bot.reply_to(message, "Используйте команду в формате /remove_user [user_number]")


bot.polling(none_stop=True)
