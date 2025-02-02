from typing import Optional

import aiohttp
import html2text
from app.databases.mongo_db import MongoDBDatabase
from bs4 import BeautifulSoup, Tag

from app.docs_process.single_process import SingleProcess
from app.models.docs import DocsContent, Link


class ExtractContentProcess(SingleProcess):
    selector: str
    selector_type: str
    selector_attrs: Optional[str] = None

    def __init__(
            self,
            mdb: MongoDBDatabase,
            order: int,
            group_id: str,
            selector: str,
            selector_type: str,
            selector_attrs: Optional[str] = None,
    ):
        super().__init__(mdb, group_id, order)
        self.selector = selector
        self.selector_type = selector_type
        self.selector_attrs = selector_attrs

    async def execute_single(self, link_obj: Link):
        link = link_obj.link
        try:
            content = await self._html_to_markdown(url=link)
            if content.strip() != "":
                if content is not None:
                    content = DocsContent(
                        base_url=link_obj.base_url,
                        link=link,
                        content=content
                    )

                    await self.mdb.add_entry(content)

            await self.mdb.update_entry(entity=link_obj, update={self.process_name: True})
        except Exception as e:
            await self.mdb.delete_entity(link_obj)
            print(f"An unexpected error occurred: {e}")

    @property
    def process_name(self) -> str:
        return "extracted"

    @property
    def process_type(self) -> str:
        return "pre"

    async def _get_beautiful_soup(
            self,
            url: str,
    ) -> Tag:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                content = await response.text()

        soup = BeautifulSoup(content, 'html.parser')
        if self.selector_type == "class" and self.selector_attrs:
            body = soup.find(self.selector, class_=self.selector_attrs) or soup.find('body')
        elif self.selector_type == "id" and self.selector_attrs:
            body = soup.find(self.selector, id=self.selector_attrs) or soup.find('body')
        else:
            body = soup.find(self.selector) or soup.find('body')
        if body is None:
            raise ValueError("No matching element found.")

        return body

    async def _html_to_markdown(self, url: str):
        body = await self._get_beautiful_soup(url=url)

        for tag in body.find_all(True):
            tag.attrs = {key: value for key, value in tag.attrs.items() if key == 'href'}

        html_content = str(body)
        markdown_converter = html2text.HTML2Text()
        markdown_converter.ignore_links = False
        markdown_converter.ignore_images = True
        markdown_converter.body_width = 0

        markdown_output = markdown_converter.handle(html_content)

        return markdown_output
