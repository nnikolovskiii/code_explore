from collections import deque
from urllib.parse import urljoin
from app.databases.mongo_db import MongoDBDatabase
from bs4 import BeautifulSoup
import requests


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

