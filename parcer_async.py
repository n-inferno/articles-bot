import asyncio
import json
import logging
from datetime import datetime
from typing import List, Tuple, Optional
from collections import namedtuple

import aiohttp
import requests
from bs4 import BeautifulSoup

URL = 'https://habr.com/ru/hub/{}/'

article = namedtuple('Post', ['header', 'date', 'link'])


def get_links(habs: List[str]) -> List[Tuple[str, str]]:
    for hub in habs:
        hub_url = URL.format(hub)
        try:
            resp = requests.get(hub_url, timeout=15)
        except Exception as e:
            logging.error(f'cannot load page {hub_url}, {e}')
            return
        logging.info(f'load {hub_url} successfully')
        soup = BeautifulSoup(resp.text, features="html.parser")
        links = []
        for i in soup.find_all('a', 'post__title_link'):
            links.append((i.text, i.get('href')))
        return links


async def post_date_evaluating(session: aiohttp.client.ClientSession, post: Tuple[str, str],
                               last_update: datetime) -> Optional:
    try:
        async with session.get(post[1], ssl=False) as resp:
            data = await resp.text()
    except Exception as e:
        logging.error(f'cannot load page {post[1]}, {e}')
        return
    soup = BeautifulSoup(data, features="html.parser")
    meta = soup.find('script', type="application/ld+json").string
    meta_dict = json.loads(meta)
    date_published = datetime.fromisoformat(meta_dict.get('datePublished'))
    return article(post[0], date_published, post[1]) if date_published > last_update else False


async def loop(hubs: List, last_update: datetime) -> List[Tuple[str, datetime, str]]:
    links = get_links(hubs)
    tasks = []
    async with aiohttp.ClientSession() as session:
        for link in links:
            task = asyncio.create_task(post_date_evaluating(session, link, last_update))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
    return [i for i in results if i]
