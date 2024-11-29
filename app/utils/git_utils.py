from git import Repo

from git import Repo

def get_last_commit(repo_path: str) -> str:
    repo = Repo(repo_path)
    last_commit = repo.head.commit
    return last_commit.hexsha


# # Initialize the repo object
# repo_path = '/home/nnikolovskii/dev/fastapi'
# repo = Repo(repo_path)
#
#
# # List all tags
# tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
# print("List of tags:")
# for tag in tags:
#     print(f"Tag: {tag.name}, Commit: {tag.commit.hexsha}, Author: {tag.commit.author.name}, Date: {tag.commit.committed_datetime}, Message: {tag.commit.message}")
