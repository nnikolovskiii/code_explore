from app.databases.mongo_db import MongoDBDatabase
from app.code_process.pre_process.file_utils import get_short_description
from app.code_process.pre_process.readme_description import create_short_description
from app.llms.generic_chat import generic_chat


def filter_content_template(
        file_path: str,
        git_repo_description: str,
        file_contents: str,
):
    return f"""Below you are given contents of a file and a description of the github repository containing the file. Your job is to determine whether the contents of the file have useful information for later user querying. The way useful is defined is whether it could help the user with coding and understanding a certain problem. 
Provide a category as well. Choose between on of these categories: "code", "documentation", "configuration", "testing" and "logging".
File name: {file_path}

Git repo description:
{git_repo_description}

File contents:
{file_contents}

First reason that return a json in the end with the following format: {{"verdict": "yer or no", "category": ""}}
"""

def filter_content(
        file_path: str,
        git_repo_description: str,
        file_contents: str
):
    template = filter_content_template(file_path, git_repo_description, file_contents)
    response = generic_chat(template)
    print(response)

mdb = MongoDBDatabase()
chunks = mdb.get_entries_dict("Chunks")
description = create_short_description(get_short_description('/home/nnikolovskii/dev/react'))
for chunk in chunks:
    file_path = chunk["file_path"]
    content = chunk["content"]
    filter_content(file_path=file_path, git_repo_description=description, file_contents=content)