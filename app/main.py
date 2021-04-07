import asyncio
import re

import aioschedule
from aiogram import Bot, Dispatcher, executor, types

from config import TOKEN
from data_managing import save_hubs, delete_user, fetch_users, get_hubs_and_update, update_date
from parcer import get_links, post_date_evaluating
from logger import logger

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def hello_handler(message: types.Message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    item1 = types.KeyboardButton('да')
    item2 = types.KeyboardButton('нет')
    markup.add(item1, item2)
    logger.info(f"User {message.from_user.id} is on server")
    await message.answer("Доброго времени суток. Рассказать что я умею?", reply_markup=markup)


async def answer_function(message):
    if message.text in ['да', 'Расскажи, что умеешь']:
        logger.info(f"User {message.from_user.id} asks what bot can do")
        markup = types.ReplyKeyboardRemove(selective=False)
        await message.answer("Могу записать интересующие тебя темы и отправлять тебе статьи по ним. "
                             "Что тебе интересно?",
                             reply_markup=markup)
        await message.answer("Названия тем можно посмотреть на сайте habr.com, я использую сокращенные обозначения"
                             " из адресной строки")
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        logger.info(f"User {message.from_user.id} is not interested in bot")
        item1 = types.KeyboardButton('Расскажи, что умеешь')
        markup.add(item1)
        await message.answer("Очень жаль :(", reply_markup=markup)


@dp.message_handler(content_types='text')
async def text_handler(message):
    if 'привет' in message.text.lower():
        return await hello_handler(message)

    elif message.text in ['да', 'Расскажи, что умеешь', 'нет']:
        return await answer_function(message)

    matching = re.findall(r'\b[a-z]*\b', message.text)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Хочу изменить хабы')
    item2 = types.KeyboardButton('Удали меня из базы')
    item3 = types.KeyboardButton('Спасибо!')
    item4 = types.KeyboardButton('Есть новые статьи?')
    markup.add(item1, item2, item3, item4)

    if message.text == 'Хочу изменить хабы':
        await message.answer("Просто пришли новые хабы :)", reply_markup=markup)

    elif message.text == 'Удали меня из базы':
        delete_user(message.from_user.id)
        del_markup = types.ReplyKeyboardRemove(selective=False)
        logger.info(f"User {message.from_user.id} deleted from database")
        await message.answer("Готово. Больше не буду слать тебе статьи.", reply_markup=del_markup)

    elif message.text == 'Спасибо!':
        logger.info(f"User {message.from_user.id} is thanking you")
        await message.answer("Всегда рад помочь!", reply_markup=markup)

    elif message.text == 'Есть новые статьи?':
        await message.answer("Сейчас посмотрю...", reply_markup=markup)
        await send_articles(message.from_user.id)

    elif any(matching):
        hubs = [i for i in matching if i]
        save_hubs(message.from_user.id, hubs)
        logger.info(f"Added hubs for user {message.from_user.id}: {hubs}")
        await message.answer("Окей, записал. Буду присылать тебе новые статьи :)", reply_markup=markup)
    else:
        logger.info(f"Text form user {message.from_user.id}: {message.text}")
        await message.answer("Не понимаю тебя :(?")


async def send_articles(user_id: str) -> None:
    hubs, date = get_hubs_and_update(user_id)
    links = await get_links(hubs)
    articles = []
    for link in links:
        data = post_date_evaluating(link, date)
        if data:
            articles.append(data)
    update_date(user_id)
    for article in articles:
        logger.info(f"Send article {article.link} for user {user_id}")
        await bot.send_message(user_id,
                               f"{article.header}\n{article.date.strftime('%d %B %Y')}\n\n{article.link}")
    if not articles:
        logger.info(f"Nothing for user {user_id}")
        await bot.send_message(user_id, "Похоже, никаких обновлений нет.")


async def pipeline() -> None:
    users = fetch_users()
    logger.info(f"Registered users: {users}")
    for user in users:
        await send_articles(user)


async def message_schedule() -> None:
    logger.info("Scheduler starting")
    aioschedule.every(5).minutes.do(pipeline)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(x) -> None:
    asyncio.create_task(message_schedule())


if __name__ == '__main__':
    logger.info("Bot starting")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)