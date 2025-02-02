from typing import List
from urllib.parse import urljoin

from bson import ObjectId

from app.databases.mongo_db import MongoDBDatabase, MongoEntry
from bs4 import BeautifulSoup
import requests
import re

from app.docs_process.process import Process
from app.models.docs import Link
from app.models.process_tracker import ProcessTracker, increment_process, update_status_process, set_end, \
    finish_process, create_process


class TraverseSitesBatch(MongoEntry):
    docs_url: str
    curr_batch: int


class TraverseSitesProcess(Process):
    patterns: List[str]

    def __init__(self, mdb: MongoDBDatabase, group_id: str, patterns: List[str]):
        super().__init__(mdb, group_id)
        self.patterns = patterns

    @property
    def process_name(self) -> str:
        return "traverse_sites"

    @property
    def process_type(self) -> str:
        return "pre"

    async def create_process_status(self) -> ProcessTracker | None:
        return await create_process(
            url=self.group_id,
            mdb=self.mdb,
            process_type="traverse",
            type="docs",
            order=1,
            group="pre"
        )

    async def execute_process(self):
        process = await self.create_process_status()

        batch = await self.mdb.get_entry_from_col_values(
            columns={"docs_url": self.group_id},
            class_type=TraverseSitesBatch,
        )

        if batch is None:
            await self.mdb.add_entry(Link(
                base_url=self.group_id,
                prev_link=self.group_id,
                link=self.group_id,
                batch=1
            ))
            new_batch = TraverseSitesBatch(docs_url=self.group_id, curr_batch=1)
            batch_id = await self.mdb.add_entry(new_batch)
            batch = await self.mdb.get_entry(ObjectId(batch_id), TraverseSitesBatch)

        print(batch)
        regex_li = []
        if self.patterns is not None:
            for pattern in self.patterns:
                regex_li.append(re.compile(pattern))

        first = True

        while True:
            if not first:
                batch.curr_batch += 1
                print(batch.curr_batch)
                await self.mdb.update_entry(batch)
            else:
                first = False

            curr_count = 0
            num_links = await  self.mdb.count_entries(Link,
                                                      {"traversed": False, "base_url": self.group_id,
                                                       "batch": batch.curr_batch})

            await update_status_process(f"Iteration: {batch.curr_batch}", process, self.mdb)
            await set_end(process, num_links, self.mdb)

            if num_links == 0:
                break

            async for link_obj in self.mdb.stream_entries(Link,
                                                          {"traversed": False, "base_url": self.group_id,
                                                           "batch": batch.curr_batch}):
                await increment_process(process=process, mdb=self.mdb, num=curr_count)
                curr_count += 1
                link_obj.traversed = True
                await  self.mdb.update_entry(link_obj)

                neighbours = self._get_neighbouring_links(link_obj.link)
                for link in neighbours:
                    link = link if link[-1] != "/" else link[:-1]
                    # regex matching
                    not_in_regex = True
                    if self.patterns is not None:
                        for regex in regex_li:
                            if regex.search(link):
                                not_in_regex = False
                                break

                    link_already_exists = await  self.mdb.get_entry_from_col_value(
                        column_name="link",
                        column_value=link,
                        class_type=Link
                    )

                    if self.group_id in link and link_already_exists is None and not_in_regex:
                        if link != self.group_id and link != self.group_id + "/":
                            li: list[str] = link.split("/")
                            if li[-1].strip() == "":
                                prev_link = "/".join(li[:-2])
                            else:
                                prev_link = "/".join(li[:-1])

                            link_obj = Link(
                                base_url=self.group_id,
                                prev_link=prev_link,
                                link=link,
                                batch=batch.curr_batch + 1
                            )
                            try:
                                await  self.mdb.add_entry(link_obj)
                            except Exception as e:
                                print(e)
                                print("*********")
                                print(link_already_exists)
                                print(link)

        await finish_process(process, self.mdb)

    @staticmethod
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
