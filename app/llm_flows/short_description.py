from app.llms.generic_chat import generic_chat


def create_short_description_template(
        readme_file: str
):
    return f"""Below you are given a README.md file of a github repository. Your job is to write a short and information dense description of the repository. USe your own knowledge as well.
Only write information on how the code in the repository can be useful for a programmer.

README.md file:
{readme_file}

Make the description short. Do not write any code.
"""

def create_short_description(
        readme_file: str
)->str:
    template = create_short_description_template(readme_file)
    response = generic_chat(template)
    print(response)

    return response


# create_short_description(get_short_description('/home/nnikolovskii/dev/react'))