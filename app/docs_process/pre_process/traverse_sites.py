import logging
from collections import deque
from typing import List
from urllib.parse import urljoin
from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import re

from app.models.docs import Link
from app.models.simple_process import SimpleProcess, update_status_process


def _get_neighbouring_links(url: str) -> set:
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all("a", href=True)

        b_url = url + "/" if not url.endswith("/") else url

        full_links = set()
        for link in links:
            li = link["href"].split("#")
            full_links.add(urljoin(b_url, li[0]))

        return full_links
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the page: {e}")
        return set()

class ProcessLink(MongoEntry):
    process: str
    link: str
    url: str
    finished: bool = False


async def traverse_links(docs_url: str, patterns:List[str],process: SimpleProcess, mdb: MongoDBDatabase):
    await mdb.add_entry(ProcessLink(process= "traverse", link=docs_url, url= docs_url))

    regex_li = []
    if patterns is not None:
        for pattern in patterns:
            regex_li.append(re.compile(pattern))

    num_iterations = 0
    while True:
        num_iterations+=1
        curr_count = 0
        num_links = await mdb.count_entries(ProcessLink, {"finished": False, "url": docs_url})
        if num_links == 0:
            break
        async for url in mdb.stream_entries(ProcessLink, {"finished":False, "url": docs_url}):
            if curr_count % 5 == 0:
                await update_status_process(f"Iteration: {num_iterations}\nProgress Bar: {curr_count}/{num_links}", process, mdb)
            url.finished = True
            await mdb.update_entry(url)
            # checked.add(url)

            neighbours = _get_neighbouring_links(url.link)
            for link in neighbours:
                not_in_regex = True
                if patterns is not None:
                    for regex in regex_li:
                        if regex.search(link):
                            not_in_regex = False
                            break
                check_link = await mdb.get_entry_from_col_values(
                    columns={"link": link},
                    class_type=ProcessLink,
                )
                if docs_url in link and check_link is None and not_in_regex:
                    # checked.add(link)
                    # links.append(link)
                    await mdb.add_entry(ProcessLink(process="traverse", link=link, url=docs_url))

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

            curr_count+=1


    link = docs_url if docs_url[-1] != "/" else docs_url[:-1]
    link_obj = Link(
        base_url=docs_url,
        prev_link=link,
        link=link,
    )
    await mdb.add_entry(link_obj)
    await mdb.delete_entries(ProcessLink, {"url": docs_url})


async def check_prev_links(docs_url: str,process: SimpleProcess, mdb: MongoDBDatabase):
    num_links = await mdb.count_entries(Link, {"base_url": docs_url})
    counter = 0
    async for link in mdb.stream_entries(Link, {"base_url": docs_url}):
        if counter % 5 == 0:
            await update_status_process(f"Progress bar: {counter}/{num_links}", process, mdb)
        counter +=1

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

async def set_parent_flags(docs_url: str,process: SimpleProcess, mdb: MongoDBDatabase):
    num_links = await mdb.count_entries(Link, {"base_url": docs_url})
    counter = 0

    async for link in mdb.stream_entries(Link, {"base_url": docs_url}):
        if counter % 5 == 0:
            await update_status_process(f"Progress bar: {counter}/{num_links}", process, mdb)
        counter +=1

        first_link_obj = await mdb.get_entry_from_col_value(
            column_name="prev_link",
            column_value=link.link,
            class_type=Link,
        )
        if first_link_obj is not None:
            link.is_parent = True
            await mdb.update_entry(link)
