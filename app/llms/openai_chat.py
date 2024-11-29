import os
from dotenv import load_dotenv
import requests
import json


def chat_with_openai(
        message: str,
        system_message: str
) -> str:
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL")
    url = 'https://api.openai.com/v1/chat/completions'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }

    data = {
        'model': openai_model,
        'messages': [
            {
                "role": "system",
                "content": system_message
            }
            ,{
                "role": "user",
                "content": message
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        response.raise_for_status()

lol = """import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit, OnDestroy {
  private ws: WebSocket | undefined;
  public messages: string = '';  // Change to a single string
  public messageText: string = '';

  ngOnInit(): void {
    this.ws = new WebSocket("ws://localhost:5000/websocket/");

    this.ws.onopen = () => {
      console.log("WebSocket connection opened.");
    };

    this.ws.onmessage = (event: MessageEvent) => {
      console.log("Message received:", event.data);
      // Concatenate the new message to the existing messages
      this.messages += event.data + " "; // Add a space for separation
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    this.ws.onclose = () => {
      console.log("WebSocket connection closed.");
    };
  }

  ngOnDestroy(): void {
    if (this.ws) {
      this.ws.close();
    }
  }

  sendMessage(event: Event): void {
    event.preventDefault();

    if (this.ws && this.messageText.trim() !== '') {
      this.ws.send(this.messageText);
      this.messageText = '';
    }
  }
}

<h1>WebSocket Chat</h1>
<form (submit)="sendMessage($event)">
  <input type="text" [(ngModel)]="messageText" name="message" autocomplete="off" />
  <button type="submit">Send</button>
</form>
<p>{{ messages }}</p> <!-- Display the concatenated messages here -->

this is my socket:
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



  formatResponse(value: any): string {
    if (typeof value === 'string') {
      // Convert Markdown-like syntax into HTML.
      let formatted = value
        .replace(/(#+) (.+)/g, (_, level, text) => `<h${level.length}>${text}</h${level.length}>`) // Headings
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>') // Bold
        .replace(/\*(.+?)\*/g, '<em>$1</em>') // Italic
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>') // Code blocks
        .replace(/\n/g, '<br>'); // Line breaks

      return formatted;
    }


How can i format the text in this way wile it streams. do you have any idea. first reason than give answer
"""



response = chat_with_openai(lol, "You are a helpful AI assistant.")
print(response)