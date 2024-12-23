import logging
from collections import deque
from urllib.parse import urljoin
from app.databases.mongo_db import MongoDBDatabase
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import re

from app.models.docs import Link


def _get_neighbouring_links(url: str) -> set:
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all("a", href=True)

        b_url = urljoin(url, '/')

        full_links = set()
        for link in links:
            li = link["href"].split("#")
            full_links.add(urljoin(b_url, li[0]))

        return full_links
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the page: {e}")
        return set()


async def traverse_links(docs_url: str, pattern:str, mdb: MongoDBDatabase):
    checked = set()
    links = deque([docs_url])

    regex = None
    if pattern is not None:
        regex = re.compile(pattern)

    while len(links) > 0:
        url = links.popleft()
        checked.add(url)

        neighbours = _get_neighbouring_links(url)
        for link in neighbours:
            not_in_regex = True
            if pattern is not None:
                not_in_regex = not regex.search(link)
            if docs_url in link and link not in checked and not_in_regex:
                checked.add(link)
                links.append(link)

                if link != docs_url and link != docs_url + "/":
                    li: list[str] =  link.split("/")
                    if li[-1].strip() == "":
                        prev_link = "/".join(li[:-2])
                    else:
                        prev_link = "/".join(li[:-1])

                    link = link if link[-1] != "/" else link[:-1]

                    link_obj = Link(
                        base_url=docs_url,
                        prev_link=prev_link,
                        link=link,
                    )
                    await mdb.add_entry(link_obj)

    link = docs_url if docs_url[-1] != "/" else docs_url[:-1]
    link_obj = Link(
        base_url=docs_url,
        prev_link=link,
        link=link,
    )
    await mdb.add_entry(link_obj)

async def check_prev_links(docs_url: str, mdb: MongoDBDatabase):
    links = await mdb.get_entries(Link, {"base_url": docs_url})

    for link in tqdm(links):
        new_prev_link = link.prev_link
        curr_link = link.prev_link
        while True:
            prev_link = await mdb.get_entry_from_col_value(
                column_name="link",
                column_value=curr_link,
                class_type=Link,
            )
            if prev_link is not None:
                new_prev_link = prev_link.link
                break

            curr_link = "/".join(curr_link.split("/")[:-1])
            logging.info(curr_link)

        if new_prev_link != link.prev_link:
            link.prev_link = new_prev_link
            await mdb.update_entry(link)

    base_link = await mdb.get_entry_from_col_value(
        column_name="link",
        column_value=docs_url if docs_url[-1] != "/" else docs_url[:-1],
        class_type=Link,
    )
    await mdb.delete_entity(base_link)

async def set_parent_flags(docs_url: str, mdb: MongoDBDatabase):
    links = await mdb.get_entries(Link, {"base_url": docs_url})

    for link in tqdm(links):
        first_link_obj = await mdb.get_entry_from_col_value(
            column_name="prev_link",
            column_value=link.link,
            class_type=Link,
        )
        if first_link_obj is not None:
            link.is_parent = True
            await mdb.update_entry(link)
# asyncio.run(check_prev_links(docs_url="https://fastapi.tiangolo.com/", mdb=MongoDBDatabase()))



