import requests

BOT_TOKEN = "7768934095:AAGq8tNLTp6toBEZW20IJi6wcazlEpJTiwk"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

try:
    response = requests.get(API_URL)
    data = response.json()

    if data.get("ok") and data.get("result"):
        unique_chats = {}  # Store unique chats as {chat_id: chat_info}

        for update in data["result"]:
            # Check if the update contains a "message" object
            if "message" in update:
                chat = update["message"]["chat"]
                chat_id = chat["id"]

                # Avoid duplicates
                if chat_id not in unique_chats:
                    unique_chats[chat_id] = {
                        "type": chat.get("type"),  # "private", "group", "supergroup", "channel"
                        "title": chat.get("title"),  # For groups/channels
                        "username": chat.get("username"),  # For users/channels
                        "first_name": chat.get("first_name"),  # For private chats
                        "last_name": chat.get("last_name"),
                    }

        # Print all unique chats
        print("Unique chats found:")
        for chat_id, info in unique_chats.items():
            print(f"Chat ID: {chat_id}")
            print(f"Type: {info['type']}")
            print(f"Title/Name: {info['title'] or info['first_name']} {info.get('last_name', '')}")
            print(f"Username: @{info['username']}" if info.get('username') else "No username")
            print("---")

    else:
        print("No updates found. Send a message to the bot or add it to a group/channel first.")

except Exception as e:
    print(f"Error: {e}")