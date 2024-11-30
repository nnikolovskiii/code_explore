
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
    except UnicodeDecodeError:
        print(f"Could not read {file_path} as a text file. It might be corrupted or have a different encoding.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

import os

def get_files_recursively(folder_name):
    file_paths = []
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            file_path = os.path.join(root, file)
            if ".git" not in file_path:
                file_paths.append(file_path)

    return file_paths


def get_files_extensions(folder_name):
    extensions = set()
    for root, dirs, files in os.walk(folder_name):
        for file in files:
            file_path = os.path.join(root, file)
            if ".git" not in file_path:
                li = file_path.split(".")
                if len(li) > 1:
                    extensions.add(li[-1])

    return extensions

def get_short_description(folder_name):
    file_path = os.path.join(folder_name, "README.md")

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    else:
        return "README.md file does not exist."

