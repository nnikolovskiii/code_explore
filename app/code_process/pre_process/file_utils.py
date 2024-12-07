import os

def _read_file(file_path) -> str | None:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def _get_all_file_paths(folder_name):
    file_paths = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            file_path = os.path.join(root, file)
            if ".git" not in file_path:
                file_paths.append(file_path)

    return file_paths


def _get_file_extension(file_path) -> str | None:
    li = file_path.split(".")
    if len(li) > 1:
        return "." + li[-1]
    return None
