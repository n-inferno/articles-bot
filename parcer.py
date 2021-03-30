from collections import namedtuple
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import locale

import requests
from bs4 import BeautifulSoup
from logger import logger

URL = 'https://habr.com/ru/hub/{}/'

article = namedtuple('Post', ['header', 'date', 'link'])


def get_links(habs: List[str]) -> List[Tuple[str, str, str]]:
    for hub in habs:
        hub_url = URL.format(hub)
        try:
            resp = requests.get(hub_url, timeout=15)
        except Exception as e:
            logger.error(f'cannot load page {hub_url}, {e}')
            return
        logger.info(f'load {hub_url} successfully')
        soup = BeautifulSoup(resp.text, features="html.parser")
        links = []
        for i, j in zip(soup.find_all('a', 'post__title_link'), soup.find_all('span', 'post__time')):
            links.append((i.text, i.get('href'), j.text))
        return links


def post_date_evaluating(post: Tuple[str, str, str], last_update: datetime) -> Optional:
    date, time = post[2].split(" в ")
    hour, minute = time.split(":")
    result = datetime.now().replace(hour=int(hour), minute=int(minute))
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    if date == 'вчера':
        result -= timedelta(days=1)
    elif date != 'сегодня':
        target = datetime.strptime(date, "%d %B %Y")
        result = result.replace(year=target.year, month=target.month, day=target.day)

    return article(post[0], result, post[1]) if result > last_update else False
