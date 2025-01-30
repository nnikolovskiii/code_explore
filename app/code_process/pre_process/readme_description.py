import asyncio
import os

from app.code_process.pre_process.file_utils import _read_file
from app.container import container
from app.llms.models import ChatLLM


def create_readme_description_template(
        readme_file: str
):
    return f"""Below you are given a README.md file of a github repository. Your job is to write a short and information dense description of the repository. Use your own knowledge as well.
Only write information on how the code in the repository can be useful for a programmer.

README.md file:
{readme_file}

Make the description short. Do not write any code.
"""

async def create_readme_description(
        readme_file: str
)->str:
    chat_service = container.chat_service()
    template = create_readme_description_template(readme_file)
    chat_llm = await chat_service.get_model(model_name="Qwen/Qwen2.5-Coder-32B-Instruct", class_type=ChatLLM)
    response = await chat_llm.generate(template)
    print(response)

    return response


async def get_short_description(folder_path: str):
    readme_path = os.path.join(folder_path, 'README.md')
    readme_content = _read_file(readme_path)
    await create_readme_description(readme_content)

asyncio.run(get_short_description('/home/nnikolovskii/dev/fastapi'))
