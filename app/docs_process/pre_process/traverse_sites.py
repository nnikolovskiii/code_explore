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
from app.models.processstatus import ProcessStatus, increment_process, update_status_process, set_end, finish_process


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


async def traverse_links(docs_url: str, patterns: List[str], process: ProcessStatus, mdb: MongoDBDatabase):
    await mdb.add_entry(Link(
        base_url=docs_url,
        prev_link=docs_url,
        link=docs_url,
        batch=1
    ))

    regex_li = []
    if patterns is not None:
        for pattern in patterns:
            regex_li.append(re.compile(pattern))

    num_iterations = 0
    while True:
        num_iterations += 1
        curr_count = 0
        num_links = await mdb.count_entries(Link, {"traversed": False, "base_url": docs_url, "batch": num_iterations})

        await update_status_process(f"Iteration: {num_iterations}", process, mdb)
        await set_end(process, num_links, mdb)

        if num_links == 0:
            break

        async for link_obj in mdb.stream_entries(Link,
                                                 {"traversed": False, "base_url": docs_url, "batch": num_iterations}):
            await increment_process(process=process, mdb=mdb, num=curr_count)
            curr_count += 1
            link_obj.traversed = True
            await mdb.update_entry(link_obj)

            neighbours = _get_neighbouring_links(link_obj.link)
            for link in neighbours:
                link = link if link[-1] != "/" else link[:-1]
                # regex matching
                not_in_regex = True
                if patterns is not None:
                    for regex in regex_li:
                        if regex.search(link):
                            not_in_regex = False
                            break

                link_already_exists = await mdb.get_entry_from_col_value(
                    column_name="link",
                    column_value=link,
                    class_type=Link
                )

                if docs_url in link and link_already_exists is None and not_in_regex:
                    if link != docs_url and link != docs_url + "/":
                        li: list[str] = link.split("/")
                        if li[-1].strip() == "":
                            prev_link = "/".join(li[:-2])
                        else:
                            prev_link = "/".join(li[:-1])

                        link_obj = Link(
                            base_url=docs_url,
                            prev_link=prev_link,
                            link=link,
                            batch=num_iterations + 1
                        )
                        try:
                            await mdb.add_entry(link_obj)
                        except Exception as e:
                            print(e)
                            print("*********")
                            print(link_already_exists)
                            print(link)

    await finish_process(process, mdb)



async def check_prev_links(docs_url: str, process: ProcessStatus, mdb: MongoDBDatabase):
    num_links = await mdb.count_entries(Link, {"base_url": docs_url})

    await set_end(process, num_links, mdb)
    counter = 0
    async for link in mdb.stream_entries(Link, {"base_url": docs_url}):
        await increment_process(process, mdb, counter)
        counter += 1

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
    await finish_process(process, mdb)


async def set_parent_flags(docs_url: str, process: ProcessStatus, mdb: MongoDBDatabase):
    num_links = await mdb.count_entries(Link, {"base_url": docs_url})
    await set_end(process, num_links, mdb)
    counter = 0

    async for link in mdb.stream_entries(Link, {"base_url": docs_url}):
        await increment_process(process, mdb, counter)
        counter += 1

        first_link_obj = await mdb.get_entry_from_col_value(
            column_name="prev_link",
            column_value=link.link,
            class_type=Link,
        )
        if first_link_obj is not None:
            link.is_parent = True
            await mdb.update_entry(link)

    await finish_process(process, mdb)
