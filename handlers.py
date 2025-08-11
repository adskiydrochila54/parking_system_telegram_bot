from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
from sqlalchemy.orm import Session
from models import *
from database import SessionLocal
from utils import generate_ticket_code
from config import TARIFF_PRICE, TARIFF_DURATION

def register_user(session: Session, telegram_id: int):
    existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if existing_user:
        return existing_user

    new_user = User(telegram_id=telegram_id)
    session.add(new_user)
    session.commit()
    return new_user

def register_start_user(bot):

    @bot.message_handler(commands=['start'])
    def start_handler(message):
        session = SessionLocal()
        register_user(session, message.chat.id)

        bot.send_message(message.chat.id, "✅ Account created successfully, Welcome!")
        session.close()

def get_finish_parking_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    button = InlineKeyboardButton("🚗 Finish Parking", callback_data="finish_parking")
    keyboard.add(button)
    return keyboard

def create_ticket_for_user(session, telegram_id):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        return None

    active_talon = session.query(Talon).filter_by(user_id=user.id, is_active=True).first()
    if active_talon:
        return active_talon

    code = generate_ticket_code()
    ticket = Talon(code=code, user_id=user.id)
    session.add(ticket)
    session.commit()
    return ticket

def register_ticket_handler(bot):
    @bot.message_handler(commands=['ticket'])
    def ticket_handler(message):
        session = SessionLocal()
        ticket = create_ticket_for_user(session, message.chat.id)
        if ticket:

            bot.send_message(message.chat.id, f"🎟 Your Ticket: {ticket.code}\nissued: {ticket.issued}",
            reply_markup=get_finish_parking_keyboard())
        else:

            bot.send_message(message.chat.id, "🚫 You are not registered, please send /start ")
            session.close()

    @bot.callback_query_handler(func=lambda call: call.data == "finish_parking")
    def finish_parking_handler(call):
        session = SessionLocal()
        user = session.query(User).filter_by(telegram_id=call.message.chat.id).first()
        if not user:

            bot.answer_callback_query(call.id, "You are not registered, please send /start ")
            session.close()
            return
        ticket = session.query(Talon).filter_by(user_id=user.id,is_active=True).order_by(Talon.issued.desc()).first()
        if not ticket:

            bot.answer_callback_query(call.id, "You do not have any active tickets, for ticket: /ticket ")
            session.close()
            return
        from datetime import datetime
        now = datetime.utcnow()
        delta = now - ticket.issued
        seconds_parked = delta.total_seconds()

        minutes = int(seconds_parked / 60)
        seconds = int(seconds_parked % 60)

        price_per_sec = TARIFF_PRICE / TARIFF_DURATION
        total_price = seconds_parked * price_per_sec
        total_price = round(total_price, 2)

        ticket.is_active = False
        session.commit()

        bot.send_message(call.message.chat.id, f"You parked for {minutes}min, {seconds} sec\nPrice: {total_price} som")
        bot.answer_callback_query(call.id)
        session.close()