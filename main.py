import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, render_template
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import threading
import time

# Telegram Bot API Token
API_TOKEN = '8015231286:AAGusBB1eTTQA3B3q8ZgUlz8l0Ksvnp1k8E'
bot = telebot.TeleBot(API_TOKEN)

# SQLite database setup
DATABASE_URL = "sqlite:///database.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# User Model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    coin_balance = Column(Integer, default=0)
    level = Column(Integer, default=1)
    referral_count = Column(Integer, default=0)
    taps_remaining = Column(Integer, default=10)  # Users can tap 10 times every hour

Base.metadata.create_all(engine)  # Create database tables

# Flask Admin Panel Setup
app = Flask(__name__)

@app.route('/admin')
def admin_panel():
    users = session.query(User).all()
    return render_template('admin.html', users=users)

# Reset taps every hour
def reset_taps():
    while True:
        users = session.query(User).all()
        for user in users:
            user.taps_remaining = 10  # Reset taps to 10
        session.commit()
        time.sleep(3600)  # Wait for 1 hour

taps_thread = threading.Thread(target=reset_taps)
taps_thread.start()

# Start Flask in a separate thread
def start_flask():
    app.run(host='0.0.0.0', port=5000)

flask_thread = threading.Thread(target=start_flask)
flask_thread.start()

# Telegram Bot Menu
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('👤 Profile'), KeyboardButton('🪙 Tap Coin'))
    markup.add(KeyboardButton('📈 Boost'), KeyboardButton('🎮 Games'))
    markup.add(KeyboardButton('💰 Wallet'), KeyboardButton('🔗 Referrals'))
    return markup

# Telegram Bot Handlers
@bot.message_handler(commands=['start'])
def start(message):
    username = message.from_user.username
    user = session.query(User).filter_by(username=username).first()
    if not user:
        user = User(username=username)
        session.add(user)
        session.commit()
    bot.send_message(
        message.chat.id, f"Welcome, {username}! Start earning coins now!", 
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text == '👤 Profile')
def profile(message):
    user = session.query(User).filter_by(username=message.from_user.username).first()
    if user:
        bot.send_message(
            message.chat.id, 
            f"👤 **Level**: {user.level}\n🪙 **Coins**: {user.coin_balance}\n🔗 **Referrals**: {user.referral_count}"
        )

@bot.message_handler(func=lambda msg: msg.text == '🪙 Tap Coin')
def tap_coin(message):
    user = session.query(User).filter_by(username=message.from_user.username).first()
    if user and user.taps_remaining > 0:
        user.coin_balance += 1
        user.taps_remaining -= 1
        session.commit()
        bot.send_message(
            message.chat.id, f"You earned a coin! 🪙 Total: {user.coin_balance} coins"
        )
    else:
        bot.send_message(
            message.chat.id, "No taps remaining! Wait for an hour for a refill."
        )

@bot.message_handler(func=lambda msg: msg.text == '🔗 Referrals')
def referrals(message):
    user = session.query(User).filter_by(username=message.from_user.username).first()
    if user:
        referral_link = f"t.me/your_bot?start={user.username}"
        bot.send_message(
            message.chat.id, 
            f"🔗 **Referral Link**: {referral_link}\n📈 **Referrals**: {user.referral_count}"
        )

# Start the Telegram Bot
bot.polling()
