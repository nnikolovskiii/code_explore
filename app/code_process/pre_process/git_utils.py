import logging
import os
from typing import Union, Tuple

from dotenv import load_dotenv
from git import Repo, GitCommandError

from app.databases.mongo_db import MongoDBDatabase
from app.models.code import GitUrl

async def clone_git_repo(
        git_url: str,
) -> str | None:
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

        return clone_dir
    except GitCommandError as e:
        logging.error(f"Git command error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

