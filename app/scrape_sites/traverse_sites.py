from collections import deque

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from app.databases.mongo.db import MongoDBDatabase
from tqdm import tqdm

from markdownify import markdownify as md

topic = """Docker is a platform that uses OS-level virtualization to package applications and their dependencies into containers. These containers are lightweight, portable, and can run consistently across different environments, from development to production. Docker provides a way to automate the deployment, scaling, and management of applications, making it easier for developers to build, ship, and run applications in any environment."""

from bs4 import BeautifulSoup
from markdownify import markdownify as md
import requests


def get_content(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Handle encoding
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.content, 'html.parser')
        body = soup.find('article') or soup.find('body')  # Fallback to <body> if <article> is not found
        if not body:
            print("No <article> or <body> tag found on the page.")
            return None

        # Resolve relative links to absolute
        for tag in body.find_all('a', href=True):
            tag['href'] = urljoin(url, tag['href'])

        # Clean up attributes
        body.attrs = {}
        for tag in body.find_all(True):
            tag.attrs = {key: value for key, value in tag.attrs.items() if key == 'href'}

        # Convert to markdown
        markdown_output = md(body.prettify(), heading_style="ATX")
        cleaned_text = re.sub(r'\n{2,}', '\n\n', markdown_output)
        return cleaned_text

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def get_neighbouring_links(url: str) -> set:
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


base_url = "https://docs.docker.com/"

def traverse_links(start_url: str):
    checked = set()
    mdb = MongoDBDatabase()
    counter = 0
    links = deque([start_url])

    while len(links) > 0:
        url = links.popleft()
        checked.add(url)

        neighbours = get_neighbouring_links(url)
        for link in neighbours:
            if base_url in link and link not in checked:
                checked.add(link)
                links.append(link)

                counter += 1
                print(counter)
                mdb.add_entry_dict({"link": link, "base_url": base_url}, "Links")


def extract_contents():
    mdb = MongoDBDatabase()
    entries = mdb.get_entries_dict("Links")
    for entry in tqdm(entries):
        link = entry["link"]
        content = get_content(link)
        if content is not None:
            mdb.add_entry_dict({"link": link, "content": content}, "Contents")
