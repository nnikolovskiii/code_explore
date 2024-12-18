from urllib.parse import urljoin
import html2text
from app.databases.mongo_db import MongoDBDatabase
from tqdm import tqdm
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import requests

from app.models.docs import DocsContent, Link


async def _get_beautiful_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.content, 'html.parser')
    body = soup.find('article') or soup.find('body')
    return body

async def _get_content(url: str) -> str | None:
    try:
        body = await _get_beautiful_soup(url)
        if not body:
            print("No <article> or <body> tag found on the page.")
            return None

        for tag in body.find_all('a', href=True):
            tag['href'] = urljoin(url, tag['href'])

        body.attrs = {}
        for tag in body.find_all(True):
            tag.attrs = {key: value for key, value in tag.attrs.items() if key == 'href'}

        compact_html = ''.join(line.strip() for line in body.prettify().splitlines())

        markdown_output = md(compact_html)

        return markdown_output

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


async def _html_to_markdown(url):
    body = await _get_beautiful_soup(url)

    for tag in body.find_all(True):
        tag.attrs = {key: value for key, value in tag.attrs.items() if key == 'href'}

    html_content = str(body)
    markdown_converter = html2text.HTML2Text()
    markdown_converter.ignore_links = False
    markdown_converter.ignore_images = True
    markdown_converter.body_width = 0

    markdown_output = markdown_converter.handle(html_content)

    return markdown_output


async def extract_contents(docs_url:str,mdb: MongoDBDatabase):
    link_objs = await mdb.get_entries(Link, {"base_url": docs_url})

    for link_obj in tqdm(link_objs):
        link = link_obj.link
        try:
            content = await _html_to_markdown(link)
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
