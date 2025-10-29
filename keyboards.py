from telebot import types

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📦 Создать сделку", "🛒 Купить подарок")
    kb.add("ℹ️ Мои сделки", "👤 Личный кабинет")
    return kb

def personal_cabinet_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💰 Баланс", callback_data="balance"),
        types.InlineKeyboardButton("📊 Рейтинг", callback_data="rating_info")
    )
    kb.add(
        types.InlineKeyboardButton("📈 Пополнить", callback_data="deposit"),
        types.InlineKeyboardButton("📉 Вывести", callback_data="withdraw")
    )
    kb.add(
        types.InlineKeyboardButton("📋 История операций", callback_data="transaction_history"),
        types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_cabinet")
    )
    return kb

def balance_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📈 Пополнить", callback_data="deposit"),
        types.InlineKeyboardButton("📉 Вывести", callback_data="withdraw"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_cabinet")
    )
    return kb

def admin_menu_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👥 Все пользователи", callback_data="admin_all_users"),
        types.InlineKeyboardButton("💰 Изменить баланс", callback_data="admin_change_balance")
    )
    kb.add(
        types.InlineKeyboardButton("❄️ Заморозить/Разморозить", callback_data="admin_toggle_freeze"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
    )
    kb.add(
        types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")
    )
    return kb

def admin_user_actions_keyboard(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💰 Изменить баланс", callback_data=f"admin_change_{user_id}"),
        types.InlineKeyboardButton("❄️ Заморозить", callback_data=f"admin_freeze_{user_id}")
    )
    kb.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back")
    )
    return kb

# Существующие клавиатуры остаются
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
