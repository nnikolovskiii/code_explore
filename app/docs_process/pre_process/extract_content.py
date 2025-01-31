from typing import Optional

import aiohttp
import html2text
from app.databases.mongo_db import MongoDBDatabase
from bs4 import BeautifulSoup, Tag

from app.models.docs import DocsContent, Link
from app.models.process_tracker import ProcessTracker, set_end, increment_process, finish_process


async def _get_beautiful_soup(
        url: str,
        selector: str,
        selector_type: str,
        selector_attrs: Optional[str] = None
) -> Tag:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            content = await response.text()

    soup = BeautifulSoup(content, 'html.parser')
    if selector_type == "class" and selector_attrs:
        body = soup.find(selector, class_=selector_attrs) or soup.find('body')
    elif selector_type == "id" and selector_attrs:
        body = soup.find(selector, id=selector_attrs) or soup.find('body')
    else:
        body = soup.find(selector) or soup.find('body')
    if body is None:
        raise ValueError("No matching element found.")

    return body


async def _html_to_markdown(url, selector: str, selector_type: str, selector_attrs: str):
    body = await _get_beautiful_soup(
        url=url,
        selector=selector,
        selector_type=selector_type,
        selector_attrs=selector_attrs
    )

    for tag in body.find_all(True):
        tag.attrs = {key: value for key, value in tag.attrs.items() if key == 'href'}

    html_content = str(body)
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False
    markdown_converter.ignore_images = True
    markdown_converter.body_width = 0

    markdown_output = markdown_converter.handle(html_content)

    return markdown_output


async def extract_contents(
        docs_url: str,
        selector: str,
        selector_type: str,
        selector_attrs: str,
        process: ProcessTracker,
        mdb: MongoDBDatabase
):
    counter = 0
    num_links = await mdb.count_entries(Link, {"base_url": docs_url})
    await set_end(process, num_links, mdb)

    async for link_obj in mdb.stream_entries(Link, {"base_url": docs_url}):
        await increment_process(process, mdb, counter)
        counter += 1

        link = link_obj.link
        try:
            content = await _html_to_markdown(
                url=link,
                selector=selector,
                selector_type=selector_type,
                selector_attrs=selector_attrs
            )
            if content.strip() != "":
                if content is not None:
                    content = DocsContent(
                        base_url=link_obj.base_url,
                        link=link,
                        content=content
                    )

                    await mdb.add_entry(content)
        except Exception as e:
            await mdb.delete_entity(link_obj)
            print(f"An unexpected error occurred: {e}")

    await finish_process(process, mdb)
