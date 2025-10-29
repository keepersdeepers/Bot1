import telebot
import sqlite3
from config import TOKEN, ADMIN_ID
from database import (
    init_db, create_deal, get_deals_by_status, update_deal_status, get_deal_by_id,
    get_or_create_user, get_user_balance, update_user_balance, get_user_rating,
    add_transaction, get_user_transactions, get_all_users, admin_update_balance,
    toggle_user_freeze, update_user_rating
)
from keyboards import (
    main_menu, buyer_confirm_keyboard, after_payment_keyboard, confirm_receive_keyboard,
    personal_cabinet_keyboard, balance_keyboard, admin_menu_keyboard, admin_user_actions_keyboard
)

bot = telebot.TeleBot(TOKEN)

init_db()

# Функция уведомления продавца
def notify_seller(deal_id, message_text):
    """Уведомляем продавца о изменении в сделке"""
    deal = get_deal_by_id(deal_id)
    if deal and deal.seller_id:
        try:
            bot.send_message(deal.seller_id, message_text)
        except Exception as e:
            print(f"Не удалось уведомить продавца {deal.seller_id}: {e}")

# -----------------------
# Команда /start
# -----------------------
@bot.message_handler(commands=['start'])
def start(msg):
    get_or_create_user(msg.from_user.id, msg.from_user.username)
    bot.send_message(msg.chat.id, "👋 Привет! Я — Гарант Бот для Telegram Gifts. MakarGarant.\n\n"
                                  "Здесь можно безопасно продавать и покупать подарки 🎁", 
                                  reply_markup=main_menu())

# -----------------------
# Личный кабинет
# -----------------------
@bot.message_handler(func=lambda message: message.text == "👤 Личный кабинет")
def personal_cabinet(message):
    user_id = message.from_user.id
    get_or_create_user(user_id, message.from_user.username)
    
    balance = get_user_balance(user_id)
    rating, deals_count = get_user_rating(user_id)
    
    text = (
        f"👤 *Личный кабинет*\n\n"
        f"💳 Баланс: *{balance:.2f}₽*\n"
        f"⭐ Рейтинг: *{rating:.1f}/5*\n"
        f"📊 Сделок завершено: *{deals_count}*\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"Выберите действие:"
    )
    
    bot.send_message(message.chat.id, text, 
                     parse_mode="Markdown",
                     reply_markup=personal_cabinet_keyboard())

# -----------------------
# Админ панель
# -----------------------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Доступ запрещен")
        return
    
    bot.send_message(message.chat.id, "⚙️ *Панель администратора*", 
                     parse_mode="Markdown",
                     reply_markup=admin_menu_keyboard())

# -----------------------
# Inline-обработчики для личного кабинета
# -----------------------
@bot.callback_query_handler(func=lambda c: c.data == "balance")
def show_balance(call):
    user_id = call.from_user.id
    balance = get_user_balance(user_id)
    
    text = (
        f"💰 *Ваш баланс*\n\n"
        f"💳 Доступно: *{balance:.2f}₽*\n\n"
        f"Вы можете пополнить баланс или вывести средства."
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=balance_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "rating_info")
def show_rating(call):
    user_id = call.from_user.id
    rating, deals_count = get_user_rating(user_id)
    
    text = (
        f"⭐ *Ваш рейтинг*\n\n"
        f"📊 Текущий рейтинг: *{rating:.1f}/5*\n"
        f"🎯 Завершенных сделок: *{deals_count}*\n\n"
        f"Рейтинг формируется на основе отзывов\n"
        f"после завершенных сделок."
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=personal_cabinet_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "transaction_history")
def show_transaction_history(call):
    user_id = call.from_user.id
    transactions = get_user_transactions(user_id, 10)
    
    if not transactions:
        text = "📋 *История операций*\n\nОпераций пока нет."
    else:
        text = "📋 *Последние операции*\n\n"
        for trans in transactions:
            amount, trans_type, description, date = trans
            emoji = "📈" if amount > 0 else "📉"
            sign = "+" if amount > 0 else ""
            text += f"{emoji} {sign}{amount:.2f}₽ - {description}\n"
            text += f"🕒 {date[:16]}\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=personal_cabinet_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "deposit")
def ask_deposit_amount(call):
    bot.send_message(call.message.chat.id, 
                    "💳 *Пополнение баланса*\n\n"
                    "Введите сумму для пополнения (например: 500):",
                    parse_mode="Markdown")
    bot.register_next_step_handler(call.message, process_deposit)

def process_deposit(message):
    try:
        amount = float(message.text)
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
            
        user_id = message.from_user.id
        update_user_balance(user_id, amount)
        add_transaction(user_id, amount, "deposit", "Пополнение баланса")
        
        bot.send_message(message.chat.id, 
                        f"✅ Баланс пополнен на *{amount:.2f}₽*\n"
                        f"💳 Текущий баланс: *{get_user_balance(user_id):.2f}₽*",
                        parse_mode="Markdown")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите корректную сумму")

@bot.callback_query_handler(func=lambda c: c.data == "withdraw")
def ask_withdraw_amount(call):
    user_id = call.from_user.id
    balance = get_user_balance(user_id)
    
    if balance <= 0:
        bot.send_message(call.message.chat.id, "❌ На балансе недостаточно средств")
        return
        
    bot.send_message(call.message.chat.id, 
                    f"💳 *Вывод средств*\n\n"
                    f"Доступно: {balance:.2f}₽\n"
                    f"Введите сумму для вывода:",
                    parse_mode="Markdown")
    bot.register_next_step_handler(call.message, process_withdraw)

def process_withdraw(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        balance = get_user_balance(user_id)
        
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
            
        if amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств на балансе")
            return
            
        update_user_balance(user_id, -amount)
        add_transaction(user_id, -amount, "withdrawal", "Вывод средств")
        
        # Уведомляем админа
        bot.send_message(ADMIN_ID,
                        f"🚨 Запрос на вывод средств\n"
                        f"👤 Пользователь: {user_id}\n"
                        f"💰 Сумма: {amount:.2f}₽\n"
                        f"💳 Баланс после вывода: {get_user_balance(user_id):.2f}₽")
        
        bot.send_message(message.chat.id, 
                        f"✅ Заявка на вывод *{amount:.2f}₽* принята!\n"
                        f"Ожидайте обработки администратором.",
                        parse_mode="Markdown")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите корректную сумму")

# -----------------------
# Админ обработчики
# -----------------------
@bot.callback_query_handler(func=lambda c: c.data == "admin_all_users")
def show_all_users(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    users = get_all_users()
    
    if not users:
        text = "👥 *Пользователи*\n\nПользователей нет."
    else:
        text = "👥 *Все пользователи*\n\n"
        for user in users:
            user_id, username, balance, rating, is_frozen = user
            status = "❄️ ЗАМОРОЖЕН" if is_frozen else "✅ АКТИВЕН"
            text += f"👤 {username or 'Без имени'} (ID: {user_id})\n"
            text += f"💰 {balance:.2f}₽ | ⭐ {rating:.1f} | {status}\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=admin_menu_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "admin_change_balance")
def ask_admin_user_id(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    bot.send_message(call.message.chat.id, 
                    "👤 Введите ID пользователя для изменения баланса:")
    bot.register_next_step_handler(call.message, ask_admin_balance_amount)

def ask_admin_balance_amount(message):
    try:
        user_id = int(message.text)
        bot.send_message(message.chat.id, 
                        f"💰 Введите сумму (для уменьшения используйте минус):")
        bot.register_next_step_handler(message, lambda m: process_admin_balance(m, user_id))
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите корректный ID пользователя")

def process_admin_balance(message, user_id):
    try:
        amount = float(message.text)
        admin_update_balance(user_id, amount)
        add_transaction(user_id, amount, "admin_adjustment", "Корректировка администратором")
        
        new_balance = get_user_balance(user_id)
        
        bot.send_message(message.chat.id,
                        f"✅ Баланс пользователя {user_id} изменен на {amount:+.2f}₽\n"
                        f"💳 Новый баланс: {new_balance:.2f}₽")
        
        # Уведомляем пользователя
        try:
            bot.send_message(user_id,
                           f"ℹ️ Ваш баланс изменен администратором\n"
                           f"📊 Изменение: {amount:+.2f}₽\n"
                           f"💳 Новый баланс: {new_balance:.2f}₽")
        except:
            pass
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите корректную сумму")

@bot.callback_query_handler(func=lambda c: c.data == "admin_toggle_freeze")
def ask_freeze_user_id(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    bot.send_message(call.message.chat.id, "👤 Введите ID пользователя для заморозки/разморозки:")
    bot.register_next_step_handler(call.message, process_admin_freeze)

def process_admin_freeze(message):
    try:
        user_id = int(message.text)
        toggle_user_freeze(user_id)
        
        # Получаем обновленные данные пользователя
        users = get_all_users()
        user_data = next((u for u in users if u[0] == user_id), None)
        
        if user_data:
            _, username, balance, rating, is_frozen = user_data
            status = "❄️ ЗАМОРОЖЕН" if is_frozen else "✅ РАЗМОРОЖЕН"
            
            bot.send_message(message.chat.id,
                           f"✅ Пользователь {username or 'Без имени'} (ID: {user_id}) {status}")
            
            # Уведомляем пользователя
            try:
                bot.send_message(user_id,
                               f"ℹ️ Ваш аккаунт был {'заморожен' if is_frozen else 'разморожен'} администратором")
            except:
                pass
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
            
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите корректный ID пользователя")

# -----------------------
# Обновление рейтинга после завершения сделки
# -----------------------
@bot.callback_query_handler(func=lambda c: c.data.startswith("received_"))
def mark_received(call):
    deal_id = int(call.data.split("_")[1])
    update_deal_status(deal_id, "completed")
    
    deal = get_deal_by_id(deal_id)
    
    # Обновляем рейтинг продавца (пока ставим автоматически 5 звезд)
    # В будущем можно добавить систему отзывов
    update_user_rating(deal.seller_id, 5)
    
    # Начисляем средства продавцу
    try:
        price = float(''.join(filter(str.isdigit, deal.price)))
        update_user_balance(deal.seller_id, price)
        add_transaction(deal.seller_id, price, "income", f"Оплата за сделку #{deal_id}")
    except:
        pass
    
    # Уведомляем продавца о завершении
    notify_seller(deal_id,
        f"🎉 Сделка завершена!\n"
        f"🎁 {deal.gift_name}\n"
        f"💰 {deal.price}\n"
        f"✅ Покупатель подтвердил получение подарка.\n"
        f"⭐ Ваш рейтинг улучшен!\n\n"
        f"Средства зачислены на ваш баланс.")
    
    bot.send_message(call.message.chat.id, 
                    "🎉 Сделка завершена! Спасибо за использование гаранта 💎")
    bot.send_message(ADMIN_ID, f"✅ Сделка #{deal_id} успешно завершена.")

# -----------------------
# Навигация
# -----------------------
@bot.callback_query_handler(func=lambda c: c.data == "back_to_cabinet")
@bot.callback_query_handler(func=lambda c: c.data == "refresh_cabinet")
def back_to_cabinet(call):
    personal_cabinet(call.message)

@bot.callback_query_handler(func=lambda c: c.data == "back_to_main")
def back_to_main(call):
    bot.send_message(call.message.chat.id, "🔙 Возврат в главное меню", 
                     reply_markup=main_menu())

# -----------------------
# Остальные существующие обработчики (мои сделки, создание сделки и т.д.)
# -----------------------
@bot.message_handler(func=lambda message: message.text == "ℹ️ Мои сделки")
def my_deals(message):
    user_id = message.from_user.id

    conn = sqlite3.connect("deals.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT id, gift_name, price, status
        FROM deals
        WHERE seller_id=? OR buyer_id=?
    """, (user_id, user_id))
    deals = cur.fetchall()
    conn.close()

    if not deals:
        bot.send_message(message.chat.id, "❌ У тебя пока нет активных сделок.", reply_markup=main_menu())
        return

    text = "📦 Твои сделки:\n\n"
    for d in deals:
        deal_id, gift_name, price, status = d
        status_text = {
            "waiting_buyer": "Ожидает покупателя",
            "waiting_payment": "Ожидает оплаты",
            "waiting_gift": "Ожидает подарок",
            "completed": "✅ Завершена",
            "dispute": "⚠️ Открыт спор",
            "cancelled": "❌ Отменена"
        }.get(status, status)
        text += f"#{deal_id} — {gift_name} ({price}₽)\nСтатус: {status_text}\n\n"

    bot.send_message(message.chat.id, text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📦 Создать сделку")
def ask_gift_name(msg):
    bot.send_message(msg.chat.id, "🎁 Введи название подарка:")
    bot.register_next_step_handler(msg, ask_price)

def ask_price(msg):
    gift_name = msg.text
    bot.send_message(msg.chat.id, "💰 Укажи цену (например, 500₽):")
    bot.register_next_step_handler(msg, lambda m: save_deal(m, gift_name))

def save_deal(msg, gift_name):
    price = msg.text
    create_deal(msg.chat.id, gift_name, price)
    bot.send_message(msg.chat.id, f"✅ Сделка создана!\nПодарок: {gift_name}\nЦена: {price}\n\n"
                                  "Теперь покупатель может её найти и купить.")

@bot.message_handler(func=lambda m: m.text == "🛒 Купить подарок")
def show_deals(msg):
    deals = get_deals_by_status("waiting_buyer")
    if not deals:
        bot.send_message(msg.chat.id, "Пока нет активных предложений 😕")
        return
    for deal in deals:
        deal_id, seller_id, gift_name, price = deal
        bot.send_message(msg.chat.id,
                         f"🎁 {gift_name}\n💰 Цена: {price}\n👤 Продавец: [{seller_id}](tg://user?id={seller_id})",
                         parse_mode="Markdown",
                         reply_markup=buyer_confirm_keyboard(deal_id))

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def confirm_buy(call):
    deal_id = int(call.data.split("_")[1])
    deal = get_deal_by_id(deal_id)
    
    # Проверка: продавец не может быть покупателем
    if call.from_user.id == deal.seller_id:
        bot.answer_callback_query(call.id, "❌ Ты не можешь купить свой же подарок.")
        return
    
    update_deal_status(deal_id, "waiting_payment", call.from_user.id)
    
    # Уведомляем продавца
    notify_seller(deal_id, 
        f"🎉 Твой подарок покупают!\n"
        f"🎁 {deal.gift_name}\n"
        f"💰 {deal.price}\n"
        f"👤 Покупатель: [{call.from_user.id}](tg://user?id={call.from_user.id})\n\n"
        f"Ожидаем оплату от покупателя...")
    
    bot.send_message(call.message.chat.id, "💳 Отправь оплату на реквизиты гаранта:\n"
                                           "`@admin_username` или TON-кошелёк.\n\n"
                                           "После оплаты — нажми 'Я оплатил'.", 
                                           parse_mode="Markdown",
                                           reply_markup=after_payment_keyboard(deal_id))
                                           
@bot.callback_query_handler(func=lambda c: c.data.startswith("paid_"))
def mark_paid(call):
    deal_id = int(call.data.split("_")[1])
    update_deal_status(deal_id, "waiting_gift")
    
    # Уведомляем продавца
    notify_seller(deal_id,
        f"💰 Покупатель оплатил подарок!\n"
        f"🎁 {get_deal_by_id(deal_id).gift_name}\n"
        f"💎 Теперь нужно отправить подарок покупателю.\n\n"
        f"После отправки — попроси покупателя подтвердить получение.")
    
    bot.send_message(call.message.chat.id, "✅ Оплата зафиксирована. Ожидаем подарок от продавца.",
                     reply_markup=confirm_receive_keyboard(deal_id))
    bot.send_message(ADMIN_ID, f"⚠️ Сделка #{deal_id} оплачена. Проверь поступление средств.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def cancel_deal(call):
    deal_id = int(call.data.split("_")[1])
    deal = get_deal_by_id(deal_id)
    
    # Проверяем, имеет ли пользователь право отменять сделку
    if call.from_user.id not in [deal.seller_id, deal.buyer_id]:
        bot.answer_callback_query(call.id, "❌ Вы не участник этой сделки")
        return
    
    update_deal_status(deal_id, "cancelled")
    
    # Уведомляем вторую сторону
    if call.from_user.id == deal.seller_id:
        notify_user = deal.buyer_id
        role = "продавец"
    else:
        notify_user = deal.seller_id
        role = "покупатель"
    
    if notify_user:
        try:
            bot.send_message(notify_user, 
                           f"❌ Сделка отменена\n"
                           f"🎁 {deal.gift_name}\n"
                           f"👤 {role} отменил сделку")
        except Exception as e:
            print(f"Не удалось уведомить пользователя {notify_user}: {e}")
    
    bot.send_message(call.message.chat.id, "❌ Сделка отменена")

@bot.callback_query_handler(func=lambda c: c.data.startswith("dispute_"))
def open_dispute(call):
    deal_id = int(call.data.split("_")[1])
    deal = get_deal_by_id(deal_id)
    update_deal_status(deal_id, "dispute")
    
    # Уведомляем вторую сторону о споре
    if call.from_user.id == deal.seller_id:
        notify_user = deal.buyer_id
        role = "продавец"
    else:
        notify_user = deal.seller_id
        role = "покупатель"
    
    if notify_user:
        try:
            bot.send_message(notify_user,
                           f"⚠️ Открыт спор по сделке\n"
                           f"🎁 {deal.gift_name}\n"
                           f"👤 {role} открыл спор\n\n"
                           f"Администратор свяжется для решения ситуации")
        except Exception as e:
            print(f"Не удалось уведомить пользователя {notify_user}: {e}")
    
    bot.send_message(ADMIN_ID, 
                    f"🚨 Открыт спор по сделке #{deal_id}\n"
                    f"🎁 {deal.gift_name}\n"
                    f"💰 {deal.price}\n"
                    f"👤 Продавец: {deal.seller_id}\n"
                    f"👤 Покупатель: {deal.buyer_id}\n"
                    f"🚩 Инициатор спора: {call.from_user.id}")
    
    bot.send_message(call.message.chat.id, "⚠️ Спор открыт. Администратор свяжется с вами.")

if __name__ == "__main__":
    print("База данных готова ✅")
    print("Бот запущен 🚀")
    bot.polling(none_stop=True)
```
