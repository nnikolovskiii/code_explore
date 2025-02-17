import asyncio

from fastapi import Request, HTTPException

from app.api.routes.auth import get_current_user

if __name__ == "__main__":
    test_token = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                  "eyJzdWIiOiJuaWtvbG92c2tpLm5pa29sYTQyQGdtYWlsLmNvbSIsImV4cCI6MTczOTMyMTM4M30."
                  "g0JZ5WzXTeeXe_Cs7zjalk8QVslLNVEYiSzEZIlqDXE")


    scope = {
        "type": "http",
        "method": "GET",
        "headers": [
            (b"cookie", f"access_token=Bearer {test_token}".encode("latin-1"))
        ],
    }

    request = Request(scope)

    try:
        current_user = asyncio.run(get_current_user(request))
        print("User found:", current_user)
    except HTTPException as exc:
        print("HTTPException:", exc.detail)