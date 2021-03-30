import re
from time import sleep

import telebot
from telebot import types

from config import TOKEN
from data_managing import save_hubs, delete_user, fetch_users, get_hubs_and_update, update_date
from parcer import get_links, post_date_evaluating
from logger import logger

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def hello_handler(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('да')
    item2 = types.KeyboardButton('нет')
    markup.add(item1, item2)
    bot.send_message(message.from_user.id, "Доброго времени суток. Рассказать что я умею?", reply_markup=markup)
    logger.info(f"User {message.from_user.id} is on server")
    bot.register_next_step_handler(message, answer_function)


def answer_function(message):
    if message.text in ['да', 'Расскажи, что умеешь']:
        logger.info(f"User {message.from_user.id} asks what bot can do")
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(message.from_user.id,
                         "Могу записать интересующие тебя темы и отправлять тебе статьи по ним. Что тебе интересно?",
                         reply_markup=markup)
        bot.send_message(message.from_user.id,
                         "<о формате тем>")
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        logger.info(f"User {message.from_user.id} is not interested in bot")
        item1 = types.KeyboardButton('Расскажи, что умеешь')
        markup.add(item1)
        bot.send_message(message.from_user.id, "Очень жаль :(", reply_markup=markup)
        bot.register_next_step_handler(message, answer_function)


@bot.message_handler(content_types='text')
def text_handler(message):
    matching = re.findall(r'\b[a-z]*\b', message.text)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Хочу изменить хабы')
    item2 = types.KeyboardButton('Удали меня из базы')
    item3 = types.KeyboardButton('Спасибо!')
    item4 = types.KeyboardButton('Есть новые статьи?')
    markup.add(item1, item2, item3, item4)

    if 'привет' in message.text.lower():
        return hello_handler(message)

    elif message.text == 'Хочу изменить хабы':
        bot.send_message(message.from_user.id, "Просто пришли новые хабы :)",
                         reply_markup=markup)

    elif message.text == 'Удали меня из базы':
        delete_user(message.from_user.id)
        del_markup = types.ReplyKeyboardRemove(selective=False)
        logger.info(f"User {message.from_user.id} deleted from database")
        bot.send_message(message.from_user.id, "Готово. Больше не буду слать тебе статьи.", reply_markup=del_markup)

    elif message.text == 'Спасибо!':
        logger.info(f"User {message.from_user.id} is thanking you")
        bot.send_message(message.from_user.id, "Всегда рад помочь!", reply_markup=markup)

    elif message.text == 'Есть новые статьи?':
        bot.send_message(message.from_user.id, "Сейчас посмотрю...", reply_markup=markup)
        send_articles(message.from_user.id)

    elif any(matching):
        hubs = [i for i in matching if i]
        save_hubs(message.from_user.id, hubs)
        logger.info(f"Added hubs for user {message.from_user.id}: {hubs}")
        bot.send_message(message.from_user.id, "Окей, записал. Буду присылать тебе новые статьи :)",
                         reply_markup=markup)
    else:
        logger.info(f"Text form user {message.from_user.id}: {message.text}")
        bot.send_message(message.from_user.id, "Не понимаю тебя :(?")


def send_articles(user_id: str) -> None:
    hubs, date = get_hubs_and_update(user_id)
    links = get_links(hubs)
    articles = []
    for link in links:
        data = post_date_evaluating(link, date)
        if data:
            articles.append(data)
    update_date(user_id)
    for article in articles:
        logger.info(f"Send article {article.link} for user {user_id}")
        bot.send_message(user_id,
                         f"{article.header}\n{article.date.strftime('%d %B %Y')}\n\n{article.link}")
    if not articles:
        logger.info(f"Nothing for user {user_id}")
        bot.send_message(user_id,
                         "Похоже, никаких обновлений нет.")


def pipeline():
    users = fetch_users()
    logger.info(f"Registered users: {users}")
    for user in users:
        send_articles(user)


if __name__ == '__main__':
    while True:
        try:
            logger.info("Bot started")
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Unsuccessful request to tg server, {e}")
            sleep(5)
