import pytest
from fastapi import HTTPException

from app.api.routes.auth import get_current_user
from app.auth.models.user import User
from app.container import container


# Dummy request that mimics FastAPI's Request (only cookies are used)
class DummyRequest:
    def __init__(self, cookies: dict):
        self.cookies = cookies


# Dummy user service to be returned by container.user_service()
class DummyUserService:
    async def get_user(self, email: str):
        # If the email matches the one in the token's payload, return a dummy user.
        if email == "nikolovskl.naikola42@gmail.com":
            return User(
                email=email,
                hashed_password="dummy_hash",
                full_name="Test User",
                is_google_auth=False
            )
        return None


@pytest.mark.asyncio
async def test_get_current_user_valid_token(monkeypatch):
    # Override the global secret and algorithm to values that will validate our test token.
    # In this example we assume that the provided token was signed using "secret" and "HS256".
    monkeypatch.setattr("app.auth.routes.secret", "secret")
    monkeypatch.setattr("app.auth.routes.algorithm", "HS256")

    # Patch container.user_service() so that it returns our DummyUserService.
    monkeypatch.setattr(container, "user_service", lambda: DummyUserService())

    # This is the token provided in the request.
    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJuaWtvbG92c2tpLm5pa29sYTQyQGdtYWlsLmNvbSIsImV4cCI6MTczOTMyMTM4M30."
        "g0JZ5WzXTeeXe_Cs7zjalk8QVslLNVEYiSzEZIlqDXE"
    )

    # Create a dummy request with the cookie "access_token" containing the token prefixed with "Bearer".
    request = DummyRequest(cookies={"access_token": f"Bearer {token}"})

    # Call the function under test.
    user = await get_current_user(request)

    # Assert that the user returned has the expected email.
    assert user.email == "nikolovskl.naikola42@gmail.com"
