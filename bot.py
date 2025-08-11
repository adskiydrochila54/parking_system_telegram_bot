import telebot
from config import TOKEN
from database import init_db
from handlers import *

bot = telebot.TeleBot(TOKEN)

register_start_user(bot)
register_ticket_handler(bot)

init_db()

bot.infinity_polling()