import telebot
import sqlite3 as sq
import time
import asyncio

def init_db():
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            telegram_id INTEGER PRIMARY KEY,
            name TEXT,
            balance INTEGER DEFAULT 500,
            level INTEGER DEFAULT 1,
            gas_level INTEGER DEFAULT 40,
            reputation INTEGER DEFAULT 90,
            last_tree_time INTEGER DEFAULT 0,
            last_tube_time INTEGER DEFAULT 0,
            passive_money INTEGER DEFAULT 0,
            last_passive_time INTEGER DEFAULT 0,
            top_place INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    connection.commit()
    cursor.close()


init_db()

bot = telebot.TeleBot("ТУТ ВАШ ТОКЕН", parse_mode=None)
def update_player_activity(telegram_id):
    """Обновляет время последней активности"""
    connection = sq.connect('game.db')
    cursor = connection.cursor()
    
    cursor.execute('''
        UPDATE players SET last_active = CURRENT_TIMESTAMP WHERE telegram_id = ?
    ''', (telegram_id,))
    
    connection.commit()
    connection.close()
@bot.message_handler(commands=['start'])
def start_message(message):
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    telegram_id = message.from_user.id
    username = message.from_user.username or f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    
    # Проверяем, существует ли игрок
    cursor.execute('SELECT * FROM players WHERE telegram_id = ?', (telegram_id,))
    existing_player = cursor.fetchone()
    
    if existing_player:
        bot.send_message(message.chat.id, "С возвращением! Ваша компания ждет ваших решений.")
        update_player_activity(telegram_id)
    else:
        # Создаем нового игрока
        try:
            cursor.execute('''
                INSERT INTO players (telegram_id, name, balance, level, gas_level, reputation) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (telegram_id, username, 500, 1, 40, 90))
            connection.commit()
            
            welcome_text = """🌍 Привет! Ты - экологически ответственная компания.

В тебя верят люди! Мир на грани катастрофы - парниковый эффект усиливается из-за корпораций. 

Тебя финансируют люди, которым не всё равно. Твои задачи:
💰 Не обанкротиться
⭐ Не потерять репутацию  
🌿 Контролировать уровень загрязнения

Используй /help для списка команд"""
            
            bot.send_message(message.chat.id, welcome_text)
            
        except sq.Error as e:
            print(f"Ошибка базы данных: {e}")
            bot.send_message(message.chat.id, "Произошла ошибка при создании профиля.")
    
    connection.close()
    
    # Проверяем условия проигрыша
    game_over = check_game_over(telegram_id)
    if game_over:
        bot.send_message(message.chat.id, f"❌ Игра окончена!\n{game_over}\n\nНачните заново с /start")
def check_game_over(telegram_id):
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    cursor.execute('SELECT balance, reputation, gas_level FROM players WHERE telegram_id = ?', 
                   (telegram_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if result:
        balance, reputation, gas_level = result
        
        if balance <= 0:
            connection = sq.connect('player.db')
            cursor = connection.cursor()
            cursor.execute('DELETE FROM players WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return "💸 Банкротство! Компания обанкротилась."
        elif reputation <= 0:
            connection = sq.connect('player.db')
            cursor = connection.cursor()
            cursor.execute('DELETE FROM players WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return "👎 Потеря доверия! Люди перестали вам доверять."
        elif gas_level >= 100:
            connection = sq.connect('player.db')
            cursor = connection.cursor()
            cursor.execute('DELETE FROM players WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return "🌫️ Экологическая катастрофа! Уровень газов достиг критической отметки."
    
    return None

@bot.message_handler(commands=['profile', 'balance', 'stats'])
def show_profile(message):
    """Показывает профиль игрока"""
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT name, balance, level, gas_level, reputation, 
               passive_money, top_place, last_active
        FROM players 
        WHERE telegram_id = ?
    ''', (telegram_id,))
    
    player = cursor.fetchone()
    connection.close()
    
    if player:
        name, balance, level, gas, reputation, passive, top_place, last_active = player
        
        # Определяем статус компании
        status = "✅ Стабильна"
        if balance < 100:
            status = "⚠️ Риск банкротства"
        if reputation < 30:
            status = "📉 Репутация падает"
        if gas > 70:
            status = "🌫️ Высокое загрязнение"
        
        response = f"🏢 КОМПАНИЯ: {name}\n"
        response += f"📊 Статус: {status}\n\n"
        response += f"💰 Баланс: {balance} монет\n"
        response += f"📈 Уровень: {level}\n"
        response += f"🌿 Загрязнение: {gas}/100\n"
        response += f"⭐ Репутация: {reputation}/100\n"
        response += f"💸 Пассивный доход: {passive}/час\n"
        response += f"🏆 Место в рейтинге: {top_place}\n"
        response += f"🕐 Последняя активность: {last_active}\n\n"
        response += "Используй /top чтобы увидеть рейтинг игроков"
    else:
        response = "Вы еще не зарегистрированы! Используйте /start"
    
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['help'])
def show_help(message):
    """Показывает справку по командам"""
    help_text = """🛠️ ДОСТУПНЫЕ КОМАНДЫ:

/start - Начать игру
/profile - Ваш профиль
/top - Рейтинг игроков
/help - Эта справка

🎮 ИГРОВОЙ ПРОЦЕСС:
- Принимайте решения, влияющие на экологию и экономику
- Балансируйте между прибылью и репутацией
- Избегайте банкротства и экологической катастрофы
- Соревнуйтесь с другими игроками"""

    bot.send_message(message.chat.id, help_text)



@bot.message_handler(commands=['top'])
def player_top(message):
    connection = sq.connect('player.db')
    cursor = connection.cursor()

    try:
        # Обновляем рейтинги перед показом топа
        cursor.execute('''
            UPDATE players 
            SET top_place = (
                SELECT COUNT(*) + 1 
                FROM players p2 
                WHERE p2.balance > players.balance
            )
        ''')
        connection.commit()

        # Получаем топ-10 игроков по балансу
        cursor.execute('''
            SELECT name, balance, level, gas_level, reputation, passive_money, top_place 
            FROM players 
            ORDER BY balance DESC 
            LIMIT 10
        ''')
        players = cursor.fetchall()

        if players:
            response = "🏆 ТОП-10 ИГРОКОВ ПО БАЛАНСУ:\n\n"
            
            for i, player in enumerate(players, 1):
                name, balance, level, gas, reputation, passive, top_place = player
                
                # Эмодзи для призовых мест
                medal = ""
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = f"{i}."
                
                response += f"{medal} {name}\n"
                response += f"   💰 {balance} монет | 📊 Ур.{level} | ⭐ {reputation}\n"
                response += f"   🌿 Загрязнение: {gas} | 💸 Пассив: {passive}/час\n\n"
            
            # Добавляем информацию о текущем игроке
            telegram_id = message.from_user.id
            cursor.execute('''
                SELECT name, balance, top_place, 
                       (SELECT COUNT(*) FROM players) as total_players
                FROM players WHERE telegram_id = ?
            ''', (telegram_id,))
            
            current_player = cursor.fetchone()
            if current_player:
                name, balance, rank, total = current_player
                response += f"——————————\n"
                response += f"👤 Ваше место: {rank}/{total}\n"
                response += f"💰 Ваш баланс: {balance} монет"
            
        else:
            response = "❌ Пока нет данных об игроках. Будьте первым!"
        
        bot.send_message(message.chat.id, response)
        
    except sq.Error as e:
        print(f"Ошибка базы данных: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при загрузке рейтинга.")
    
    finally:
        connection.close()
@bot.message_handler(commands=['do'])
def what_do(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if result:
            player_level = result[0]
            if player_level == 1:
                bot.send_message(message.chat.id, "Ты можешь посадить деревья, пропиши команду /grow_tree за 10 eco_coin")
            elif player_level >= 2:
                bot.send_message(message.chat.id, "Ты можешь выпустить видео ролик в grow_tube /grow_tube за 40 eco_coin")
                bot.send_message(message.chat.id, "Ты можешь посадить деревья, пропиши команду /grow_tree за 10 eco_coin")
        else:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()
    game_over = check_game_over(telegram_id)
    if game_over:
        bot.send_message(message.chat.id, f"❌ Игра окончена!\n{game_over}")

@bot.message_handler(commands=['grow_tree'])
def grow_tree(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT last_tree_time, balance, level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        last_tree_time, balance, level = result
        current_time = int(time.time())
        
        if level < 1:
            bot.send_message(message.chat.id, "❌ Недостаточный уровень для этого действия!")
            return
        
        if current_time - last_tree_time < 300:
            remaining = 300 - (current_time - last_tree_time)
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
        
        if balance >= 10:
            cursor.execute('''
                UPDATE players 
                SET balance = balance - 10,
                    gas_level = gas_level - 2,
                    reputation = reputation + 2,
                    level = level + 1,
                    last_tree_time = ?
                WHERE telegram_id = ?
            ''', (current_time, telegram_id))
            
            connection.commit()
            bot.send_message(message.chat.id, 
                "🌳 Дерево посажено!\n"
                "💰 Balance -10\n" 
                "⛽ Gas level -2\n" 
                "⭐ Reputation +2\n" 
                "🎯 Level +1")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()
    
    game_over = check_game_over(telegram_id)
    if game_over:
        bot.send_message(message.chat.id, f"❌ Игра окончена!\n{game_over}")

@bot.message_handler(commands=['grow_tube'])
def grow_tube(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT last_tube_time, balance, level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        last_tube_time, balance, level = result
        current_time = int(time.time())
        
        if level < 2:
            bot.send_message(message.chat.id, "❌ Недостаточный уровень для этого действия!")
            return
        
        if current_time - last_tube_time < 500:
            remaining = 500 - (current_time - last_tube_time)
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
        
        if balance >= 40:
            cursor.execute('''
                UPDATE players 
                SET balance = balance - 40,
                    gas_level = gas_level - 3,
                    reputation = reputation + 1,
                    passive_money = passive_money + 10,
                    last_tube_time = ?
                WHERE telegram_id = ?
            ''', (current_time, telegram_id))
            
            connection.commit()
            bot.send_message(message.chat.id, 
                "🎥 Видео выложено!\n"
                "💰 Balance -40\n" 
                "⛽ Gas level -3\n" 
                "⭐ Reputation +1\n" 
                "💵 Passive money +10\n"
                'Теперь ты можешь прописать команду /money для получения пассивного дохода')
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()
    
    game_over = check_game_over(telegram_id)
    if game_over:
        bot.send_message(message.chat.id, f"❌ Игра окончена!\n{game_over}")
@bot.message_handler(commands=['help'])
def collect_money(message):
    bot.send_message(message.chat.id, "/do-список команд,/start-создание компании, /balance-твои характеристики")
@bot.message_handler(commands=['money'])
def collect_money(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT last_passive_time, passive_money FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        last_passive_time, passive_money = result
        current_time = int(time.time())
        
        if current_time - last_passive_time < 60:
            remaining = 60 - (current_time - last_passive_time)
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
        
        if passive_money >= 5:
            cursor.execute('''
                UPDATE players 
                SET balance = balance + ?,
                    reputation = reputation - 1,
                    last_passive_time = ?
                WHERE telegram_id = ?
            ''', (passive_money, current_time, telegram_id))
            
            connection.commit()
            bot.send_message(message.chat.id, 
                f"💰 Получено пассивного дохода: {passive_money} eco coin\n" 
                "⭐ Reputation -1")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно пассивного дохода")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()
    
    game_over = check_game_over(telegram_id)
    if game_over:
        bot.send_message(message.chat.id, f"❌ Игра окончена!\n{game_over}")

bot.infinity_polling()
