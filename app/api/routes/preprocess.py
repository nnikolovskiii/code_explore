from fastapi import FastAPI, HTTPException, APIRouter
from app.databases.mongo.db import MongoDBDatabase
from git import Repo, GitCommandError
import os
import logging

from app.models.git_url import GitUrl
from app.utils.git_utils import get_last_commit

logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

@router.get("/clone_library/")
async def clone_library(git_url: str):
    mdb = MongoDBDatabase("library_explore")
    urls = mdb.get_entries(GitUrl, doc_filter={"url": git_url})

    if len(urls) > 0:
        return {"message": "Repository URL is already saved."}, 200

    folder_name = git_url.split(".git")[0].split("/")[-1]
    clone_dir = f"/home/nnikolovskii/dev/{folder_name}"

    parent_dir = os.path.dirname(clone_dir)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
        logging.debug(f"Created parent directory: {parent_dir}")

    try:
        Repo.clone_from(git_url, clone_dir)
        logging.debug(f"Repository cloned successfully to {clone_dir}")

        mdb.add_entry(GitUrl(
            url=git_url,
            path=clone_dir,
            last_commit=get_last_commit(clone_dir)
        ))

        return {"message": "Repository cloned successfully."}, 201
    except GitCommandError as e:
        logging.error(f"Git command error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid git URL or repository cannot be cloned: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")