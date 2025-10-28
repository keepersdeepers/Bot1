from telebot import types

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📦 Создать сделку", "🛒 Купить подарок", "ℹ️ Мои сделки")
    return kb

def buyer_confirm_keyboard(deal_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Купить", callback_data=f"buy_{deal_id}")
    )
    return kb

def after_payment_keyboard(deal_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("💰 Я оплатил", callback_data=f"paid_{deal_id}"),
        types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{deal_id}")
    )
    return kb

def confirm_receive_keyboard(deal_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🎁 Подарок получил", callback_data=f"received_{deal_id}"),
        types.InlineKeyboardButton("⚠️ Открыть спор", callback_data=f"dispute_{deal_id}")
    )
    return kb