from copy import deepcopy
from typing import List, Any, Dict

from app.databases.mongo.db import MongoDBDatabase
from app.flows.preprocess import get_files_recursively, read_file
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from app.llm_flows.chunk_transform import summarize_chunk, short_description
from app.llm_flows.extract_contents import extract_contents


async def chunk(entries:List[Dict[str, Any]], key:str, collection_name:str):
    mdb = MongoDBDatabase()
    # tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-72B-Instruct")
    #
    # def token_length(text):
    #     return len(tokenizer.encode(text))

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=30000,
        chunk_overlap=200,
        length_function=len,
    )

    for entry in tqdm(entries):
        content = entry[key]
        text_splitter.split_text(content)
        tokenized_content = tokenizer.encode(content)
        num_tokens = len(tokenized_content)
        entity = deepcopy(entry)
        entity.pop(key)
        if num_tokens >= 30000:
            li = text_splitter.split_text(content)
            for i, elem in enumerate(li):
                entity["content"] = elem
                entity["order"] = i
                mdb.add_entry_dict(entity, collection_name)

        else:
            entity["content"] = content
            mdb.add_entry_dict(entity, collection_name)

def chunk_github_files():
    mdb = MongoDBDatabase()

    extensions = mdb.get_unique_values("Extensions", "name")
    file_paths = get_files_recursively("/home/nnikolovskii/dev/react")

    li = []
    for file_path in tqdm(file_paths):
        if "." + file_path.split(".")[-1] in extensions:
            content = read_file(file_path)
            new_dict = {"file_path": file_path, "content": content}
            li.append(new_dict)


    chunk(li, "content", "GithubChunks")

def chunk_documentation_files():
    mdb = MongoDBDatabase()
    li = mdb.get_entries_dict("Contents")

    chunk(li, "content", "DocumentationChunks")


def add_summarization(chunk_type: str, key: str, num_of_chunks: int):
    mdb = MongoDBDatabase()
    chunks = mdb.get_entries_dict(chunk_type)
    di = {}
    for chunk in chunks:
        id = chunk[key]
        if id not in di:
            di[id] = []
        di[id].append(chunk)

    for id, li in tqdm(di.items(), total=len(di.items())):
        if len(li) > 1:
            sorted_li = sorted(li, key=lambda x: x['order'])
            chunks = sorted_li[:num_of_chunks]
            summary = ""
            for chunk in tqdm(chunks):
                content = chunk["content"]
                summary += summarize_chunk(content)
                summary += "\n\n"

            desc = short_description(summary)

            mdb.add_entry_dict({"desc": desc, key: id}, "Summaries")

            for chunk in li:
                content = chunk["content"]
                new_content = "Topic: " + desc + "\n\n" + content
                chunk["content"] = new_content

                mdb.update_entity_dict(chunk, chunk_type)

def refine_doc_chunks_with_llm():
    mdb = MongoDBDatabase()
    chunks = mdb.get_entries_dict("DocumentationChunks")
    for chunk in tqdm(chunks):
        content = chunk["content"]
        link = chunk["link"]
        new_content = extract_contents(content)
        mdb.add_entry_dict({"prev_content": content, "content": new_content, "link": link}, "DocumentationRefinedChunks")


refine_doc_chunks_with_llm()