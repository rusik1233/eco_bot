from telebot import types 
import telebot
import sqlite3 as sq
import time
import asyncio
from config import TOKEN
import random
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
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            location TEXT DEFAULT 'city',
            last_go_time INTEGER DEFAULT 0,
            last_interview_time INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            last_work_time INTEGER DEFAULT 0,
            last_herbs_time INTEGER DEFAULT 0,
            last_recycle_time INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            company_name TEXT,
            amount INTEGER,
            category TEXT,
            invest_time INTEGER,
            FOREIGN KEY (telegram_id) REFERENCES players (telegram_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            quest_type TEXT,
            progress INTEGER DEFAULT 0,
            target INTEGER,
            reward INTEGER,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (telegram_id) REFERENCES players (telegram_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS level_rewards (
            telegram_id INTEGER,
            level INTEGER,
            claimed INTEGER DEFAULT 0,
            PRIMARY KEY (telegram_id, level),
            FOREIGN KEY (telegram_id) REFERENCES players (telegram_id)
        )
    ''')
    connection.commit()
    cursor.close()

init_db()

bot = telebot.TeleBot(TOKEN, parse_mode=None)


companies = {}
selected_company = None
selected_True = False
current_category = None
def update_player_activity(telegram_id):

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
    

    cursor.execute('SELECT * FROM players WHERE telegram_id = ?', (telegram_id,))
    existing_player = cursor.fetchone()
    
    if existing_player:
        bot.send_message(message.chat.id, "С возвращением! Ваша компания ждет ваших решений.")
        update_player_activity(telegram_id)
    else:

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
    help_text = """🛠️ ДОСТУПНЫЕ КОМАНДЫ:

🎮 ОСНОВНЫЕ:
/start - Начать игру
/profile - Ваш профиль
/top - Рейтинг игроков
/do - Список доступных действий
/guide - Руководство по игре

🌳 ДЕЙСТВИЯ:
/grow_tree - Посадить деревья
/grow_tube - Снять видео
/interview - Дать интервью
/money - Собрать пассивный доход

💼 ИНВЕСТИЦИИ:
/invest - Инвестировать в компании
/get_profit - Получить доход от инвестиций

📍 ЛОКАЦИИ:
/location - Текущая локация
/go - Список перемещений
/go_city - Перейти в город
/go_forest - Перейти в лес
/go_industrial_zone - Перейти в промзону

🎁 БОНУСЫ:
/daily - Ежедневная награда
/news - Экологические новости
/quests - Квесты
/claim_quest - Получить награду за квест
/level_rewards - Награды за уровни
/claim_level - Получить награду за уровень

🎯 ЦЕЛЬ ИГРЫ:
• Не обанкротиться (баланс > 0)
• Не потерять репутацию (> 0)
• Контролировать загрязнение (< 100)"""

    bot.send_message(message.chat.id, help_text)



@bot.message_handler(commands=['top'])
def player_top(message):
    connection = sq.connect('player.db')
    cursor = connection.cursor()

    try:

        cursor.execute('''
            UPDATE players 
            SET top_place = (
                SELECT COUNT(*) + 1 
                FROM players p2 
                WHERE p2.balance > players.balance
            )
        ''')
        connection.commit()

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
        cursor.execute('SELECT level, location FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if result:
            player_level, location = result
            
            actions = []
            if player_level >= 1:
                actions.append("🌳 /grow_tree - посадить деревья (10 eco coin)")
            if player_level >= 2:
                actions.append("🎥 /grow_tube - снять видео (40 eco coin)")
            if player_level >= 10:
                actions.append("📺 /interview - дать интервью (60 eco coin)")
            
            actions.append("💰 /money - собрать пассивный доход")
            actions.append("💼 /invest - инвестировать в компании")
            actions.append("💵 /get_profit - получить доход от инвестиций")
            actions.append("🎁 /daily - ежедневная награда")
            actions.append("📰 /news - экологические новости")
            
            if location == 'city':
                actions.append("\n🏙️ ДЕЙСТВИЯ В ГОРОДЕ:")
                actions.append("🏢 /work_office - работать в офисе (50 eco coin)")
                actions.append("🛒 /buy_supplies - купить расходники (30 eco coin)")
                actions.append("📊 /market_research - исследование рынка (25 eco coin)")
                actions.append("🤝 /networking - нетворкинг (40 eco coin)")
                
            elif location == 'forest':
                actions.append("\n🌲 ДЕЙСТВИЯ В ЛЕСУ:")
                actions.append("🌿 /collect_herbs - собрать травы (15 eco coin)")
                actions.append("🦋 /study_wildlife - изучить дикую природу (35 eco coin)")
                actions.append("🏕️ /eco_camp - эко-лагерь (60 eco coin)")
                actions.append("📸 /nature_photo - фотосессия природы (20 eco coin)")
                
            elif location == 'industrial_zone':
                actions.append("\n🏭 ДЕЙСТВИЯ В ПРОМЗОНЕ:")
                actions.append("♻️ /recycle_waste - переработать отходы (80 eco coin)")
                actions.append("🔬 /tech_research - технические исследования (100 eco coin)")
                actions.append("⚡ /energy_audit - энергоаудит (70 eco coin)")
                actions.append("🛠️ /repair_equipment - ремонт оборудования (90 eco coin)")
            
            message_text = f"📍 Локация: {location}\n\n" + "\n".join(actions)
            bot.send_message(message.chat.id, message_text)
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

@bot.message_handler(commands=['work_office'])
def work_office(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance, last_work_time FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance, last_work_time = result
        current_time = int(time.time())
        
        if location != 'city':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в городе!")
            return
            
        if current_time - (last_work_time or 0) < 300:
            remaining = 300 - (current_time - (last_work_time or 0))
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
            
        if balance >= 50:
            cursor.execute('''
                UPDATE players 
                SET balance = balance - 50 + 80, 
                    reputation = CASE WHEN reputation + 1 > 100 THEN 100 ELSE reputation + 1 END,
                    gas_level = CASE WHEN gas_level + 1 > 100 THEN 100 ELSE gas_level + 1 END,
                    last_work_time = ? 
                WHERE telegram_id = ?
            ''', (current_time, telegram_id))
            connection.commit()
            bot.send_message(message.chat.id, "🏢 Поработали в офисе!\n💰 -50 +80 eco coin\n⭐ Reputation +1\n⛽ Gas level +1")
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

@bot.message_handler(commands=['collect_herbs'])
def collect_herbs(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance, last_herbs_time FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance, last_herbs_time = result
        current_time = int(time.time())
        
        if location != 'forest':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в лесу!")
            return
            
        if current_time - (last_herbs_time or 0) < 200:
            remaining = 200 - (current_time - (last_herbs_time or 0))
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
            
        if balance >= 15:
            cursor.execute('''
                UPDATE players 
                SET balance = balance - 15 + 35, 
                    gas_level = CASE WHEN gas_level - 1 < 0 THEN 0 ELSE gas_level - 1 END,
                    last_herbs_time = ? 
                WHERE telegram_id = ?
            ''', (current_time, telegram_id))
            connection.commit()
            bot.send_message(message.chat.id, "🌿 Собрали лечебные травы!\n💰 -15 +35 eco coin\n⛽ Gas level -1")
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

@bot.message_handler(commands=['recycle_waste'])
def recycle_waste(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance, last_recycle_time FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance, last_recycle_time = result
        current_time = int(time.time())
        
        if location != 'industrial_zone':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в промзоне!")
            return
            
        if current_time - (last_recycle_time or 0) < 400:
            remaining = 400 - (current_time - (last_recycle_time or 0))
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
            
        if balance >= 80:
            cursor.execute('''
                UPDATE players 
                SET balance = balance - 80 + 150, 
                    gas_level = CASE WHEN gas_level - 3 < 0 THEN 0 ELSE gas_level - 3 END,
                    reputation = CASE WHEN reputation + 2 > 100 THEN 100 ELSE reputation + 2 END,
                    last_recycle_time = ? 
                WHERE telegram_id = ?
            ''', (current_time, telegram_id))
            connection.commit()
            bot.send_message(message.chat.id, "♻️ Переработали отходы!\n💰 -80 +150 eco coin\n⛽ Gas level -3\n⭐ Reputation +2")
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

@bot.message_handler(commands=['grow_tree'])
def grow_tree(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT last_tree_time, balance, level, gas_level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        last_tree_time, balance, level, gas_level = result
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
                    gas_level = CASE WHEN gas_level - 2 < 0 THEN 0 ELSE gas_level - 2 END,
                    reputation = CASE WHEN reputation + 2 > 100 THEN 100 ELSE reputation + 2 END,
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
            update_quest_progress(telegram_id, 'plant_trees')
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
правильный_ответ = None
@bot.message_handler(commands=['grow_tube'])
def grow_tube(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT last_tube_time, balance, level, gas_level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        last_tube_time, balance, level, gas_level = result
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
                    gas_level = CASE WHEN gas_level - 3 < 0 THEN 0 ELSE gas_level - 3 END,
                    reputation = CASE WHEN reputation + 1 > 100 THEN 100 ELSE reputation + 1 END,
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
            update_quest_progress(telegram_id, 'make_videos')
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


@bot.message_handler(commands=['interview'])
def interview(message):
    global правильный_ответ
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT last_interview_time, balance, level, gas_level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        last_interview_time, balance, level, gas_level = result
        current_time = int(time.time())

        if level < 10:
            bot.send_message(message.chat.id, "вы не слишком популярная компания нужен уровень 10")
            return
        
        if current_time - last_interview_time < 500:
            remaining = 500 - (current_time - last_interview_time)
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
        
        if balance > 60: 
            ecology_questions = [
    {
        "question": "Что такое парниковый эффект?",
        "correct_answer": "Процесс задержки тепловой энергии",
        "wrong_answers": [
            "Процесс охлаждения за счет облаков",
            "Способ очистки воздуха"
        ]
    },
    {
        "question": "Какой газ составляет основную долю парниковых газов?",
        "correct_answer": "Двуокись углерода (CO2)",
        "wrong_answers": [
            "Кислород (O2)",
            "Азот (N2)"
        ]
    },
    {
        "question": "Что означает термин 'биоразнообразие'?",
        "correct_answer": "Разнообразие живых организмов",
        "wrong_answers": [
            "Количество биологических отходов",
            "Скорость размножения организмов"
        ]
    },
    {
        "question": "Какие основные источники загрязнения океана?",
        "correct_answer": "Пластиковые отходы",
        "wrong_answers": [
            "Космический мусор,",
            "Радиоволны,"
        ]
    }
]


            random_qa = random.choice(ecology_questions)
            вопрос = random_qa["question"]
            правильный_ответ = random_qa["correct_answer"]
            неверный_ответ1 = random_qa["wrong_answers"][0]
            неверный_ответ2 = random_qa["wrong_answers"][1]

            spisok = [правильный_ответ, неверный_ответ1, неверный_ответ2]
            random.shuffle(spisok)

            markup = types.InlineKeyboardMarkup()

            for answer in spisok:
                button = types.InlineKeyboardButton(text=answer, callback_data=f"answer:{answer}")
                markup.add(button)
            bot.send_message(message.chat.id, вопрос, reply_markup=markup)
            connection.commit()
            

    finally:
        cursor.execute('UPDATE players SET last_interview_time = ? WHERE telegram_id = ?', (current_time, telegram_id))
        connection.commit()
        cursor.close()
        connection.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('answer'))
def handle_answer(call):
    global правильный_ответ
    telegram_id = call.message.chat.id
    selected = call.data[len('answer:'):]
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        if selected == правильный_ответ:
            bot.send_message(call.message.chat.id, '🎉 Молодец! Правильный ответ.')
            bot.delete_message(call.message.chat.id, call.message.message_id)
            cursor.execute('''
                    UPDATE players 
                    SET balance = balance + 40,
                        reputation = CASE WHEN reputation + 5 > 100 THEN 100 ELSE reputation + 5 END,
                        passive_money = passive_money + 10,
                        gas_level = CASE WHEN gas_level - 1 < 0 THEN 0 ELSE gas_level - 1 END
                    WHERE telegram_id = ?
                ''', (telegram_id,))
            connection.commit()
            bot.send_message(call.message.chat.id, 
                    "🎥Викторина пройдена\n"
                    "💰 Balance +40\n" 
                    "⭐ Reputation +5\n" 
                    "💵 Passive money +10\n"
                    "⛽ Gas level -1\n"
                    'Теперь ты можешь прописать команду /money для получения пассивного дохода')
        else:
            cursor.execute('SELECT balance, reputation FROM players WHERE telegram_id = ?', (telegram_id,))
            result = cursor.fetchone()
            if result:
                balance, reputation = result
                if balance >= 40 and reputation >= 5:
                    cursor.execute('''
                            UPDATE players 
                            SET balance = balance - 40,
                                reputation = reputation - 5
                            WHERE telegram_id = ?
                        ''', (telegram_id,))
                    connection.commit()
                    bot.send_message(call.message.chat.id, 
                            "🎥 Викторина проиграна\n"
                            "💰 Balance -40\n" 
                            "⭐ Reputation -5\n" )
                else:
                    bot.send_message(call.message.chat.id, "❌ Недостаточно средств или репутации для штрафа!")
            bot.send_message(call.message.chat.id, f"❌ Неправильно. Правильный ответ: {правильный_ответ}.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
    finally:
        cursor.close()
        connection.close()
    
    game_over = check_game_over(telegram_id)
    if game_over:
        bot.send_message(call.message.chat.id, f"❌ Игра окончена!\n{game_over}")




@bot.message_handler(commands=['help'])
def collect_money(message):
    bot.send_message(message.chat.id, "/do-список команд,/start-создание компании, /balance-твои характеристики")



@bot.message_handler(commands=['money'])
def collect_money(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT last_passive_time, passive_money, reputation FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        last_passive_time, passive_money, reputation = result
        current_time = int(time.time())
        
        if current_time - last_passive_time < 60:
            remaining = 60 - (current_time - last_passive_time)
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {remaining} секунд")
            return
        
        if passive_money >= 5:
            if reputation > 1:
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
                update_quest_progress(telegram_id, 'earn_money', passive_money)
            else:
                cursor.execute('''
                    UPDATE players 
                    SET balance = balance + ?,
                        last_passive_time = ?
                    WHERE telegram_id = ?
                ''', (passive_money, current_time, telegram_id))
                
                connection.commit()
                bot.send_message(message.chat.id, 
                    f"💰 Получено пассивного дохода: {passive_money} eco coin\n" 
                    "⭐ Reputation уже минимальная")
                update_quest_progress(telegram_id, 'earn_money', passive_money)
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
@bot.message_handler(commands=['location'])
def check_location(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT location FROM players WHERE telegram_id = ?', (telegram_id, ))
        result = cursor.fetchone()

        if result:
            location = result[0]
            bot.send_message(message.chat.id, f"📍 Текущая локация: {location} пропиши команду /go для пермещения")
        else:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['go'])
def go_loc(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT level, location FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return

        level, location = result
        
        message_text = f"📍 Текущая локация: {location}\n\n🚶 ДОСТУПНЫЕ ПЕРЕМЕЩЕНИЯ:\n\n"
        
        message_text += "🏙️ /go_city - Перейти в город (10 eco coin)\n"
        
        if level >= 10:
            message_text += "🌲 /go_forest - Перейти в лес (10 eco coin, уровень 10+)\n"
        else:
            message_text += "🔒 Лес - нужен 10 уровень\n"
            
        if level >= 20:
            message_text += "🏭 /go_industrial_zone - Перейти в промзону (10 eco coin, уровень 20+)\n"
        else:
            message_text += "🔒 Промзона - нужен 20 уровень\n"
            
        bot.send_message(message.chat.id, message_text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()



def go_any(telegram_id, new_loc , cost, min_level=0):
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        resultss = ''
        cursor.execute('SELECT last_go_time, balance, level, location FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        if not result:
            resultss = "❌ Игрок не найден!"
            return resultss
        
        last_go_time, balance, level, location = result
        
        current_time = int(time.time())
        
        if current_time - last_go_time < 60:
            remaining = 60 - (current_time - last_go_time)
            resultss +=f"⏳ Перезарядка: {remaining} секунд"
            return resultss
        if location == new_loc:
            resultss += f"Ты уже в {new_loc}"
        elif location != new_loc and balance >= cost and level >= min_level :
            cursor.execute('''
                UPDATE players 
                SET balance = balance - ?,
                    last_go_time = ?,
                    location = ?,
                    gas_level = CASE WHEN gas_level + 1 > 100 THEN 100 ELSE gas_level + 1 END
                WHERE telegram_id = ?
            ''', (cost, current_time, new_loc, telegram_id))
            connection.commit()
            resultss += f'Ты переместился в локацию {new_loc}\n⛽ Gas level +1 (транспорт)'
        elif balance < cost:
            resultss +=f'У Тебя недостаточно денег на проезд стоимость {cost}'
        elif level < min_level:
            resultss += f'У Тебя недостаточный уровень для проезда на проезд в {new_loc} нужный уровень {min_level}'


    except Exception as e:
        resultss += f"Ошибка: {e}"
        return resultss
    finally:
        cursor.close()
        connection.close()
        
        game_over = check_game_over(telegram_id)
        if game_over:
            resultss += f"\n\n❌ Игра окончена!\n{game_over}"
        
        return resultss


@bot.message_handler(commands=['go_city'])
def go_city(message):
    telegram_id = message.from_user.id
    result = go_any(telegram_id,'city',cost=10, min_level=0)
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['go_forest'])
def go_forest(message):
    telegram_id = message.from_user.id
    result = go_any(telegram_id,'forest',cost=10, min_level=10)
    if result: 
        bot.send_message(message.chat.id, result)
    else:
            bot.send_message(message.chat.id, 'не получилось')


@bot.message_handler(commands=['go_industrial_zone'])
def go_industrial_zone(message):
    telegram_id = message.from_user.id
    result = go_any(telegram_id,'industrial_zone',cost=10, min_level=20)
    if result:
        bot.send_message(message.chat.id, result)
    else:
        bot.send_message(message.chat.id, 'не получилось')

        
all_companies = {
    'Зелёные': {
        "солнечная_электростанция": 150, "ветряная_ферма": 120, "завод_переработки": 200,
        "органическая_ферма": 80, "эко_туризм": 90, "производство_биотоплива": 180,
        "завод_по_опреснению": 220, "компания_велосипедов": 60, "эко_строительство": 110,
        "производство_эко_упаковки": 70, "солнечные_панели": 140, "эко_транспорт": 95
    },
    'Средние': {
        "производство_карандашей": 100, "IT_компания": 130, "образовательный_центр": 85,
        "кафе_здорового_питания": 95, "ремонтная_мастерская": 65, "локальный_маркет": 75,
        "дизайн_студия": 110, "издательство": 120, "медицинский_центр": 140,
        "транспортная_компания": 160, "строительная_фирма": 125, "рекламное_агентство": 105
    },
    'Красные': {
        "нефтяная_компания": 300, "угольная_шахта": 250, "химический_завод": 280,
        "цементный_завод": 200, "автопроизводитель": 230, "авиакомпания": 270,
        "судостроительная_верфь": 190, "металлургический_комбинат": 260, "пластиковый_завод": 170,
        "мясной_комбинат": 150, "табачная_фабрика": 220, "нефтеперерабатывающий_завод": 320
    },
    'Уникальные': {
        "тюрьма": 1000, "космическая_компания": 5000, "научная_лаборатория": 3200,
        "фондовая_биржа": 4000, "крипто_ферма": 1080, "искусственный_интеллект": 3050,
        "квантовые_технологии": 900, "биотехнологии": 1050, "нанотехнологии": 5050
    }
}

available_companies = {}
last_update_time = 0

def update_available_companies():
    global available_companies, last_update_time
    current_time = int(time.time())
    
    if current_time - last_update_time < 180:
        return
        
    available_companies = {}
    
    for name, price in all_companies['Зелёные'].items():
        if random.random() < 0.35:
            available_companies[name] = {'price': price, 'category': 'Зелёные'}
            
    for name, price in all_companies['Средние'].items():
        if random.random() < 0.25:
            available_companies[name] = {'price': price, 'category': 'Средние'}
            
    for name, price in all_companies['Красные'].items():
        if random.random() < 0.10:
            available_companies[name] = {'price': price, 'category': 'Красные'}
            
    for name, price in all_companies['Уникальные'].items():
        if random.random() < 0.01:
            available_companies[name] = {'price': price, 'category': 'Уникальные'}
            
    last_update_time = current_time
@bot.message_handler(commands=['invest'])
def invest(message):
    update_available_companies()
    
    if not available_companies:
        bot.send_message(message.chat.id, "📈 Биржа временно закрыта! Попробуйте через несколько минут.")
        return
        
    available_categories = set()
    for company_data in available_companies.values():
        available_categories.add(company_data['category'])
    
    markup = types.InlineKeyboardMarkup()
    
    if 'Зелёные' in available_categories:
        button1 = types.InlineKeyboardButton(text='💚 Зелёные', callback_data="category_Зелёные")
        markup.add(button1)
    if 'Средние' in available_categories:
        button2 = types.InlineKeyboardButton(text='🟡 Средние', callback_data="category_Средние")
        markup.add(button2)
    if 'Красные' in available_categories:
        button3 = types.InlineKeyboardButton(text='🔴 Красные', callback_data="category_Красные")
        markup.add(button3)
    if 'Уникальные' in available_categories:
        button4 = types.InlineKeyboardButton(text='💎 Уникальные', callback_data="category_Уникальные")
        markup.add(button4)
        
    next_update = 180 - (int(time.time()) - last_update_time)
    
    bot.send_message(message.chat.id, 
        f'📊 ФОНДОВАЯ БИРЖА\n\n'
        f'⏰ Обновление через: {next_update} сек\n\n'
        'Доступные категории акций:', 
        reply_markup=markup)
    
@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def handle_category_selection(call):
    global companies, current_category
    category = call.data.replace('category_', '')
    current_category = category
    chat_id = call.message.chat.id
    
    category_companies = {}
    for name, data in available_companies.items():
        if data['category'] == category:
            category_companies[name] = data['price']
    
    if not category_companies:
        bot.send_message(chat_id, f"❌ В категории '{category}' нет доступных акций!")
        return
        
    companies = category_companies
    
    category_emoji = {
        'Зелёные': '💚',
        'Средние': '🟡', 
        'Красные': '🔴',
        'Уникальные': '💎'
    }
    
    message_text = f"{category_emoji.get(category, '')} АКЦИИ '{category.upper()}':\n\n"
    message_text += "📈 ДОСТУПНЫЕ:\n"
    
    for name, price in category_companies.items():
        message_text += f"• {name}: {price} eco coin\n"
        
    unavailable = []
    for name in all_companies[category]:
        if name not in available_companies:
            unavailable.append(name)
            
    if unavailable:
        message_text += "\n📉 НЕДОСТУПНЫЕ:\n"
        for name in unavailable[:5]:
            message_text += f"• {name}\n"
        if len(unavailable) > 5:
            message_text += f"• ... и ещё {len(unavailable) - 5}\n"
    
    message_text += "\n💡 Напишите название акции для покупки"
        
    global selected_True 
    selected_True = True

    bot.send_message(chat_id, message_text)

@bot.message_handler(commands=['get_profit'])
def get_investment_profit(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT company_name, amount, category FROM investments WHERE telegram_id = ?', (telegram_id,))
        investments = cursor.fetchall()
        
        if not investments:
            bot.send_message(message.chat.id, "❌ У вас нет активных инвестиций!")
            return
            
        total_profit = 0
        results = []
        
        for company_name, amount, category in investments:
            if category == 'Зелёные':
                multiplier = random.uniform(0.75, 1.5)
            elif category == 'Средние':
                multiplier = random.uniform(0.5, 1.75)
            elif category == 'Красные':
                multiplier = random.uniform(0.25, 2.0)
            else:
                multiplier = random.uniform(0.25, 2.0)
                
            profit = int(amount * multiplier)
            total_profit += profit
            
            if multiplier > 1:
                emoji = "📈"
            elif multiplier < 1:
                emoji = "📉"
            else:
                emoji = "➡️"
                
            results.append(f"{emoji} {company_name}: {profit} eco coin (x{multiplier:.2f})")
        
        cursor.execute('UPDATE players SET balance = balance + ? WHERE telegram_id = ?', (total_profit, telegram_id))
        cursor.execute('DELETE FROM investments WHERE telegram_id = ?', (telegram_id,))
        connection.commit()
        
        message_text = "💰 Результаты инвестиций:\n\n" + "\n".join(results)
        message_text += f"\n\n💵 Общий доход: {total_profit} eco coin"
        bot.send_message(message.chat.id, message_text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()
@bot.message_handler(commands=['daily'])
def daily(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()

    try:
        cursor.execute('SELECT last_daily FROM players WHERE telegram_id = ?', (telegram_id, ))
        result = cursor.fetchone()

        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return

        last_daily = result[0]

        current_time = int(time.time())

        if current_time - last_daily < 86400:
            remaining = 86400 - (current_time - last_daily)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            bot.send_message(message.chat.id, f"⏳ Перезарядка: {hours} часов и {minutes} минут")
        else:
            cursor.execute('UPDATE players SET balance = balance + 100, last_daily = ? WHERE telegram_id = ?', (current_time, telegram_id))
            connection.commit()
            bot.send_message(message.chat.id, "✅ Вы получили 100 eco coin за день!")

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()


@bot.message_handler(commands=['news'])
def news(message):
    eco_news = [
    "🌍 Сегодня мировое сообщество договорилось сократить выбросы парниковых газов на 30% к 2030 году.",
    "🐠 На берегу Океана обнаружена новая роща кораллов, которая восстанавливается благодаря усилиям добровольцев.",
    "♻️ Учёные разработали инновационный способ переработки пластиковых отходов в энергию.",
    "🧹 Местные жители устроили субботник по очистке реки, собрав за день тонны мусора.",
    "🌬️ В результате глобальных инициатив уровень загрязнения воздуха в мегаполисах снизился на 15%.",
    "🗑️ Изучение показывает, что урны и раздельный сбор мусора увеличивают переработку отходов на 25%.",
    "⚡ Компания объявила о намерении полностью перейти на использование возобновляемых источников энергии к 2025 году.",
    "🦋 В национальном парке успешно восстановлена популяция редких видов растений и животных.",
    "🚌 Значительные инвестиции выделены на развитие общественного транспорта и велосипедных дорожек.",
    "🥤 Международное соглашение о запрете использования односторонних пластиковых стаканчиков вступило в силу.",
    "🤖 В некоторых городах уже внедрена система «умных» мусорных контейнеров, отслеживающих заполненность.",
    "🧪 Учёные разработали экологически чистый пластик, разлагающийся за несколько месяцев.",
    "👥 Молодёжные организации проводят акции по раздельному сбору отходов для школьников и студентов.",
    "🌳 В результате недавней кампании по деревосберегающим технологиям количество вырубленных деревьев уменьшилось на 20%.",
    "☀️ Изобретатели создали солнечные панели нового поколения, увеличивающие КПД до 25%.",
    "🏞️ Экологический туризм становится всё более популярным, стимулируя сохранение природы.",
    "🔋 Местные сообщества внедряют программы по переработке использованных батарей и аккумуляторов.",
    "🌊 В некоторых регионах начались проекты по восстановлению болот и водно-болотных угодий для борьбы с засухой и повышения биоразнообразия.",
    "🐢 Образовательные кампании повышают осведомлённость о вреде пластика для морской жизни.",
    "🚗 Рост использования электромобилей помогает снизить уровень загрязнения воздуха в мегаполисах.",
    "🏢 Города внедряют зеленые крыши и вертикальные сады для улучшения экологии и снижения температуры.",
    "🦁 Международные организации объявили о новых целях по сохранению редких видов животных и растений.",
    "🌞 В развивающихся странах началось масштабное внедрение солнечной энергетики для борьбы с энергодефицитом.",
    "🌲 Исследования показывают, что восстановление лесов помогает снижать уровень CO2 в атмосфере.",
    "🚫 В некоторых странах вводят штрафы за использование одноразовой пластиковой посуды.",
    "🌱 Команды ученых создают биорастения, поглощающие загрязнения из воздуха и воды.",
    "🛍️ Проводятся кампании по снижению использования пластиковых пакетов и контейнеров в магазинах.",
    "🌊 Международные проекты по очистке океанов собирают тонны пластика и мусора.",
    "📚 Красочные кампании по просвещению о важности сохранения биоразнообразия проходят в школах и университетах.",
    "💻 Разрабатываются технологии по утилизации электронных отходов, опасных для окружающей среды.",
    "🚜 В сельской местности запускаются программы по использованию органических удобрений и экологического земледелия.",
    "🎨 Городские парки украшают новые экологичные инсталляции и арт-объекты из переработанных материалов.",
    "🏛️ Экологический приоритет стал частью городской политики, включающей модернизацию инфраструктуры.",
    "🤖 Искусственный интеллект помогает оптимизировать маршруты доставки и снизить выбросы транспортных средств.",
    "🏭 Многие компании вводят программы экологической ответственности и устойчивого развития.",
    "✊ Общественники и активисты продолжают бороться за сохранение редких природных территорий.",
    "🏠 Строительство новых экологичных жилых комплексов продолжается с учетом зеленых стандартов.",
    "👗 Экологическая мода и использование переработанных материалов становятся трендом среди дизайнеров."
]
    selected_news = random.choice(eco_news)
    bot.send_message(message.chat.id, f"📰 ЭКОЛОГИЧЕСКИЕ НОВОСТИ:\n\n{selected_news}")
    

@bot.message_handler(commands=['buy_supplies'])
def buy_supplies(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'city':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в городе!")
            return
            
        if balance >= 30:
            cursor.execute('UPDATE players SET balance = balance - 30 + 20, reputation = reputation + 1 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "🛒 Купили расходники!\n💰 -30 +20 eco coin\n⭐ Reputation +1")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['market_research'])
def market_research(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'city':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в городе!")
            return
            
        if balance >= 25:
            cursor.execute('UPDATE players SET balance = balance - 25 + 40, level = level + 1 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "📊 Провели исследование рынка!\n💰 -25 +40 eco coin\n🎯 Level +1")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['networking'])
def networking(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'city':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в городе!")
            return
            
        if balance >= 40:
            cursor.execute('UPDATE players SET balance = balance - 40 + 60, passive_money = passive_money + 5 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "🤝 Провели нетворкинг!\n💰 -40 +60 eco coin\n💵 Passive money +5")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['study_wildlife'])
def study_wildlife(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'forest':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в лесу!")
            return
            
        if balance >= 35:
            cursor.execute('UPDATE players SET balance = balance - 35 + 55, reputation = reputation + 2 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "🦋 Изучили дикую природу!\n💰 -35 +55 eco coin\n⭐ Reputation +2")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['eco_camp'])
def eco_camp(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'forest':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в лесу!")
            return
            
        if balance >= 60:
            cursor.execute('UPDATE players SET balance = balance - 60 + 100, gas_level = gas_level - 2, reputation = reputation + 3 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "🏕️ Организовали эко-лагерь!\n💰 -60 +100 eco coin\n⛽ Gas level -2\n⭐ Reputation +3")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()
interview
@bot.message_handler(commands=['nature_photo'])
def nature_photo(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'forest':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в лесу!")
            return
            
        if balance >= 20:
            cursor.execute('UPDATE players SET balance = balance - 20 + 35, passive_money = passive_money + 3 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "📸 Провели фотосессию природы!\n💰 -20 +35 eco coin\n💵 Passive money +3")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['tech_research'])
def tech_research(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'industrial_zone':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в промзоне!")
            return
            
        if balance >= 100:
            cursor.execute('UPDATE players SET balance = balance - 100 + 180, level = level + 2 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "🔬 Провели технические исследования!\n💰 -100 +180 eco coin\n🎯 Level +2")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['energy_audit'])
def energy_audit(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'industrial_zone':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в промзоне!")
            return
            
        if balance >= 70:
            cursor.execute('UPDATE players SET balance = balance - 70 + 120, gas_level = gas_level - 4, reputation = reputation + 1 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "⚡ Провели энергоаудит!\n💰 -70 +120 eco coin\n⛽ Gas level -4\n⭐ Reputation +1")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['repair_equipment'])
def repair_equipment(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT location, balance FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        location, balance = result
        
        if location != 'industrial_zone':
            bot.send_message(message.chat.id, "❌ Эта команда доступна только в промзоне!")
            return
            
        if balance >= 90:
            cursor.execute('UPDATE players SET balance = balance - 90 + 140, passive_money = passive_money + 8 WHERE telegram_id = ?', (telegram_id,))
            connection.commit()
            bot.send_message(message.chat.id, "🛠️ Отремонтировали оборудование!\n💰 -90 +140 eco coin\n💵 Passive money +8")
        else:
            bot.send_message(message.chat.id, "❌ Недостаточно средств!")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

def create_quest(telegram_id, quest_type, target, reward):
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO quests (telegram_id, quest_type, target, reward) VALUES (?, ?, ?, ?)', 
                   (telegram_id, quest_type, target, reward))
    connection.commit()
    cursor.close()
    connection.close()

def update_quest_progress(telegram_id, quest_type, progress_add=1):
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE quests SET progress = progress + ? WHERE telegram_id = ? AND quest_type = ? AND completed = 0', 
                   (progress_add, telegram_id, quest_type))
    connection.commit()
    cursor.close()
    connection.close()

@bot.message_handler(commands=['quests'])
def show_quests(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT quest_type, progress, target, reward, completed FROM quests WHERE telegram_id = ?', (telegram_id,))
        quests = cursor.fetchall()
        
        if not quests:
            create_quest(telegram_id, 'plant_trees', 5, 100)
            create_quest(telegram_id, 'make_videos', 3, 150)
            create_quest(telegram_id, 'earn_money', 1000, 200)
            bot.send_message(message.chat.id, "🎯 Квесты созданы! Пропишите /quests снова")
            return
            
        message_text = "🎯 ВАШИ КВЕСТЫ:\n\n"
        
        for quest_type, progress, target, reward, completed in quests:
            if completed:
                status = "✅ Выполнен"
            else:
                status = f"{progress}/{target}"
                
            if quest_type == 'plant_trees':
                message_text += f"🌳 Посадить деревья: {status} (🎁 {reward} eco coin)\n"
            elif quest_type == 'make_videos':
                message_text += f"🎥 Снять видео: {status} (🎁 {reward} eco coin)\n"
            elif quest_type == 'earn_money':
                message_text += f"💰 Заработать денег: {status} (🎁 {reward} eco coin)\n"
                
        message_text += "\n💵 /claim_quest - Получить награду"
        bot.send_message(message.chat.id, message_text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['claim_quest'])
def claim_quest_reward(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT quest_type, progress, target, reward FROM quests WHERE telegram_id = ? AND completed = 0 AND progress >= target', (telegram_id,))
        completed_quests = cursor.fetchall()
        
        if not completed_quests:
            bot.send_message(message.chat.id, "❌ Нет выполненных квестов!")
            return
            
        total_reward = 0
        claimed_quests = []
        
        for quest_type, progress, target, reward in completed_quests:
            cursor.execute('UPDATE quests SET completed = 1 WHERE telegram_id = ? AND quest_type = ?', (telegram_id, quest_type))
            cursor.execute('UPDATE players SET balance = balance + ? WHERE telegram_id = ?', (reward, telegram_id))
            total_reward += reward
            
            if quest_type == 'plant_trees':
                claimed_quests.append(f"🌳 Посадка деревьев")
            elif quest_type == 'make_videos':
                claimed_quests.append(f"🎥 Съёмка видео")
            elif quest_type == 'earn_money':
                claimed_quests.append(f"💰 Заработок")
                
        connection.commit()
        
        message_text = f"🎉 Получены награды!\n\n" + "\n".join(claimed_quests)
        message_text += f"\n\n💵 Общая награда: {total_reward} eco coin"
        bot.send_message(message.chat.id, message_text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['level_rewards'])
def show_level_rewards(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        current_level = result[0]
        
        level_rewards = {
            5: 200, 10: 500, 15: 800, 20: 1200, 25: 1500,
            30: 2000, 35: 2500, 40: 3000, 45: 3500, 50: 5000
        }
        
        message_text = f"🎆 НАГРАДЫ ЗА УРОВНИ (текущий: {current_level}):\n\n"
        
        for level, reward in level_rewards.items():
            cursor.execute('SELECT claimed FROM level_rewards WHERE telegram_id = ? AND level = ?', (telegram_id, level))
            claimed_result = cursor.fetchone()
            
            if current_level >= level:
                if claimed_result and claimed_result[0] == 1:
                    status = "✅ Получено"
                else:
                    status = "🎁 Доступно"
            else:
                status = "🔒 Недоступно"
                
            message_text += f"🎯 Уровень {level}: {reward} eco coin - {status}\n"
            
        message_text += "\n💵 /claim_level - Получить награду за уровень"
        bot.send_message(message.chat.id, message_text)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['claim_level'])
def claim_level_reward(message):
    telegram_id = message.from_user.id
    connection = sq.connect('player.db')
    cursor = connection.cursor()
    
    try:
        cursor.execute('SELECT level FROM players WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        
        if not result:
            bot.send_message(message.chat.id, "❌ Игрок не найден!")
            return
            
        current_level = result[0]
        
        level_rewards = {
            5: 200, 10: 500, 15: 800, 20: 1200, 25: 1500,
            30: 2000, 35: 2500, 40: 3000, 45: 3500, 50: 5000
        }
        
        claimed_rewards = []
        total_reward = 0
        
        for level, reward in level_rewards.items():
            if current_level >= level:
                cursor.execute('SELECT claimed FROM level_rewards WHERE telegram_id = ? AND level = ?', (telegram_id, level))
                claimed_result = cursor.fetchone()
                
                if not claimed_result or claimed_result[0] == 0:
                    cursor.execute('INSERT OR REPLACE INTO level_rewards (telegram_id, level, claimed) VALUES (?, ?, 1)', (telegram_id, level))
                    cursor.execute('UPDATE players SET balance = balance + ? WHERE telegram_id = ?', (reward, telegram_id))
                    claimed_rewards.append(f"🎯 Уровень {level}: {reward} eco coin")
                    total_reward += reward
                    
        if claimed_rewards:
            connection.commit()
            message_text = f"🎉 Получены награды!\n\n" + "\n".join(claimed_rewards)
            message_text += f"\n\n💵 Общая награда: {total_reward} eco coin"
            bot.send_message(message.chat.id, message_text)
        else:
            bot.send_message(message.chat.id, "❌ Нет доступных наград!")
        
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")
    finally:
        cursor.close()
        connection.close()

@bot.message_handler(commands=['guide'])
def guide(message):
    guide_text = """📖 РУКОВОДСТВО ПО ИГРЕ:

🌱 Пропишите команду /help для списка команд
🌳 Сначала садите деревья для поднятия уровня
🎥 Начиная с 2 уровня вы можете снимать видео что повысит ваш доход
💰 Собирайте деньги, садите деревья, инвестируйте
📍 Используйте /location чтобы узнать где вы находитесь
🚶 Перемещайтесь между локациями для новых возможностей
🎯 Выполняйте квесты и получайте награды за уровни!"""
    bot.send_message(message.chat.id, guide_text)


    
@bot.message_handler(content_types=['text'])
def handle_text(message):
    global selected_company, selected_True, current_category
    if selected_True:
        if message.text in companies:
            telegram_id = message.from_user.id
            selected_company = message.text
            investment_cost = companies[message.text]
            
            connection = sq.connect('player.db')
            cursor = connection.cursor()
            
            try:
                cursor.execute('SELECT balance FROM players WHERE telegram_id = ?', (telegram_id,))
                result = cursor.fetchone()
                
                if not result:
                    bot.send_message(message.chat.id, "❌ Игрок не найден!")
                    return
                    
                balance = result[0]
                
                if balance >= investment_cost:
                    cursor.execute('UPDATE players SET balance = balance - ? WHERE telegram_id = ?', (investment_cost, telegram_id))
                    cursor.execute('INSERT INTO investments (telegram_id, company_name, amount, category, invest_time) VALUES (?, ?, ?, ?, ?)',(telegram_id, selected_company, investment_cost, current_category, int(time.time())))
                    connection.commit()
                    
                    bot.send_message(message.chat.id, 
                        f"✅ Успешно инвестировано {investment_cost} eco coin в {selected_company}!\nИспользуйте /get_profit для получения дохода")
                else:
                    bot.send_message(message.chat.id, 
                        f"❌ Недостаточно средств! Нужно: {investment_cost} eco coin")
                        
            except Exception as e:
                bot.send_message(message.chat.id, f"Ошибка: {e}")
            finally:
                cursor.close()
                connection.close()
                selected_True = False
        else:
            bot.send_message(message.chat.id, "❌ Неверное название компании!")
            selected_True = False
bot.infinity_polling()
