from bson import ObjectId
from tqdm import tqdm
from app.databases.singletons import get_mongo_db
from app.llms.json_response import get_json_response
from app.models.preprocess import Content, DocumentChunk, Context, Category, FinalDocumentChunk


def add_context_template(
        context: str,
        chunk_text: str
):
    return f"""<document> 
{context}
</document> 
Here is the chunk we want to situate within the whole document which is part of a code documentation.
<chunk> 
{chunk_text} 
</chunk> 
Give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Also determine the category of the chunk: "navigational", "release_notes" or "content".
Return in json format: {{"context": "...", "category": "..."}}
"""

def add_category_template(
        chunk_text: str
):
    return f"""Below you are given a document which is part of a code documentation.
<document> 
{chunk_text} 
</document> 

Your job is to determine the category of the chunk: "navigational", "release_notes" or "content".
Return in json format: {{"category": "..."}}
"""

async def _get_surrounding_context(
        chunk:DocumentChunk,
        content: Content,
        context_len:int
) -> str:
    start_index = chunk.start_index
    end_index = chunk.end_index
    content = content.content

    tmp1 = min(end_index + context_len, len(content))
    tmp2 = max(start_index - context_len, 0)

    if tmp2 == 0:
        tmp1 = min(end_index + context_len + (context_len-start_index), len(content))

    if tmp1 == len(content):
        tmp2 = max(start_index - context_len - (context_len - (len(content) - end_index)), 0)

    after_context = content[end_index:tmp1] + "..."
    before_context = "..." + content[tmp2:start_index]

    return before_context + chunk.content + after_context


async def add_context(
    chunk: DocumentChunk,
    context_len: int
):
    mdb = await get_mongo_db()
    content = await mdb.get_entity(ObjectId(str(chunk.content_id)),Content)
    content_len = len(content.content)

    if len(content.content) != chunk.end_index and chunk.start_index == 0:
        context = await _get_surrounding_context(chunk, content, context_len)
        template = add_context_template(context=context, chunk_text=chunk.content)
        response = await get_json_response(template, system_message="You are an AI assistant designed in providing contextual summaries and categorize documents.")
        await mdb.add_entry(Context(
            chunk_id=chunk.id,
            context=response["context"],
        ))
        await mdb.add_entry(Category(
            chunk_id=chunk.id,
            name=response["category"],
        ))
    else:
        template = add_category_template(chunk_text=chunk.content)
        response = await get_json_response(template,
                                           system_message="You are an AI assistant designed in providing contextual summaries and categorize documents.")
        await mdb.add_entry(Category(
            chunk_id=chunk.id,
            name=response["category"],
        ))

async def add_context_flow():
    mdb = await get_mongo_db()
    await mdb.delete_collection("Context")
    await mdb.delete_collection("Category")

    chunks = await mdb.get_entries(DocumentChunk)

    for chunk in tqdm(chunks[2553:]):
        try:
            await add_context(chunk, 8000)
        except Exception as e:
            print(e)



async def create_final_chunks():
    mdb = await get_mongo_db()
    chunks = await mdb.get_entries(DocumentChunk)
    contexts = await mdb.get_entries(Context)
    contexts_dict = {context.chunk_id: context.context for context in contexts}
    categories = await mdb.get_entries(Category)
    categories_dict = {category.chunk_id: category.category for category in categories}

    count=0
    for chunk in tqdm(chunks):
        new_dict = {"chunk_id": chunk.id, "content": chunk.content}

        if chunk.id in contexts_dict:
            new_dict["content"] = contexts_dict[chunk.id] + new_dict["content"]
            count+=1

        new_dict["category"] = categories_dict[chunk.id]
        final_chunk = FinalDocumentChunk(**new_dict)
        await mdb.add_entry(final_chunk)

    print(count/len(chunks)*100)

# asyncio.run(add_context_flow())