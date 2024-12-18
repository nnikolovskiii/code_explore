from fastapi import APIRouter
import asyncio

from fastapi import WebSocket

from app.chat.chat import chat
import logging

from app.stream_llms.hf_inference_stream import chat_with_hf_inference_stream
import json
logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            data = json.loads(data)
            message, user_messages, assistant_messages = data
            print(message)
            print(user_messages)
            print(assistant_messages)

            history = []
            for i in range(len(user_messages)):
                history.append({"role": "user", "content": user_messages[i]})
                if i < len(assistant_messages):
                    history.append({"role": "user", "content": assistant_messages[i]})


            async for response_chunk in chat_with_hf_inference_stream(
                message=message,
                system_message="You are a expert code AI assistant which provides factually correct, detailed and step-by-step answers for users questions.",
                history=history,
                stream=True,
            ):
                # print(f"Sending chunk: {response_chunk}")
                await websocket.send_text(response_chunk)
                await asyncio.sleep(0.1)

            await websocket.send_text("<ASTOR>")
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error: {e}")
            break