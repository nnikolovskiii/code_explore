import logging
import os
from typing import Union, Tuple

from dotenv import load_dotenv
from git import Repo, GitCommandError

from app.databases.mongo_db import MongoDBDatabase
from app.models.code import GitUrl

async def clone_git_repo(
        mdb: MongoDBDatabase,
        git_url: str,
        override: bool
) -> Tuple[bool, str]:
    if not override:
        urls = await mdb.get_entries(GitUrl, doc_filter={"url": git_url})

        if len(urls) > 0:
            return True, "The git repo already exists."

    folder_name = git_url.split(".git")[0].split("/")[-1]
    load_dotenv()
    root_git_path = os.getenv("ROOT_GIT_PATH")
    clone_dir = f"{root_git_path}/{folder_name}"

    parent_dir = os.path.dirname(clone_dir)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
        logging.debug(f"Created parent directory: {parent_dir}")

    try:
        Repo.clone_from(git_url, clone_dir)
        logging.debug(f"Repository cloned successfully to {clone_dir}")

        await mdb.add_entry(GitUrl(
            url=git_url,
            path=clone_dir,
        ))

        return True, "Successfully cloned the git repo."
    except GitCommandError as e:
        logging.error(f"Git command error: {e}")
        return False, f"Invalid git URL or repository cannot be cloned: {e}"
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False, f"An unexpected error occurred: {e}"