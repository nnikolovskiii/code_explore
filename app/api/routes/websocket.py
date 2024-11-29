from fastapi import APIRouter
import asyncio

from fastapi import WebSocket

from app.llms.hf_inference_chat import chat_with_hf_inference
import logging


logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            async for response_chunk in chat_with_hf_inference(
                message=data,
                system_message="You are a helpful AI assistant.",
                stream=True,
            ):
                print(f"Sending chunk: {response_chunk}")
                await websocket.send_text(response_chunk)
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error: {e}")
            break