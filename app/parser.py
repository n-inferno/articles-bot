import asyncio
from collections import namedtuple
from datetime import datetime, timedelta
from typing import List, Tuple, Union
import locale

import aiohttp
from bs4 import BeautifulSoup
from logger import logger

URL = 'https://habr.com/ru/hub/{}/'

article = namedtuple('Post', ['header', 'date', 'link'])


async def get_content(url: str, session: aiohttp.ClientSession) -> str:
    async with session.get(url) as resp:
        data = await resp.read()
        logger.info(f'load {url} successfully')
        return data


async def get_links(habs: List[str]) -> List[Tuple[str, str, str]]:
    tasks = []

    async with aiohttp.ClientSession() as session:
        for hub in habs:
            hub_url = URL.format(hub)
            task = asyncio.create_task(get_content(hub_url, session))
            tasks.append(task)
        texts = await asyncio.gather(*tasks)

    for text in texts:
        soup = BeautifulSoup(text, features="html.parser")
        sorted_links = []
        for i, j in zip(soup.find_all('a', 'post__title_link'), soup.find_all('span', 'post__time')):
            sorted_links.append((i.text, i.get('href'), j.text))
        return sorted_links


def post_date_evaluating(post: Tuple[str, str, str], last_update: datetime) -> Union[bool, article]:
    date, time = post[2].split(" в ")
    hour, minute = time.split(":")
    result = datetime.now().replace(hour=int(hour), minute=int(minute), second=0)
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    if date == 'вчера':
        result -= timedelta(days=1)
    elif date != 'сегодня':
        target = datetime.strptime(date, "%d %B %Y")
        result = result.replace(year=target.year, month=target.month, day=target.day)

    return article(post[0], result, post[1]) if result > last_update else False
