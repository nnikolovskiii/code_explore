import asyncio
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.params import Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import jwt
from app.auth.models.user import User
from app.container import container
from datetime import datetime, timedelta, timezone
from jwt.exceptions import PyJWTError
from pydantic import EmailStr
from fastapi import Request

router = APIRouter()
load_dotenv()
secret = os.getenv("JWT_SECRET")
algorithm = os.getenv("ALGORITHM")

class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: str

@router.post("/register")
async def register(
        user_data: UserRegistration
):
    mdb = container.mdb()
    user_service = container.user_service()
    password_service = container.password_service()
    user_exists = await user_service.get_user(user_data.email)
    if user_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        hashed_password=password_service.get_password_hash(user_data.password),
        full_name=user_data.full_name,
        is_google_auth=False
    )
    await mdb.add_entry(new_user)

    return {"message": "Registration successful"}

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(
        user_data: UserLogin
):
    user_service = container.user_service()
    password_service = container.password_service()

    user = await user_service.get_user(user_data.email)
    print(user)
    if not user or not password_service.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_google_auth:
        raise HTTPException(status_code=400, detail="Use Google login")

    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    jwt_token = jwt.encode(
        {"sub": user.email, "exp": expires},
        secret,
        algorithm=algorithm,
    )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {jwt_token}",
        httponly=True,
        max_age=1800,
    )

    print(jwt_token)
    return response


async def get_current_user(
        request: Request,
) -> User:
    user_service = container.user_service()

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = token.strip().removeprefix("Bearer").strip()
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    user = await user_service.get_user(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

if __name__ == "__main__":
    # The provided JWT token
    test_token = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                  "eyJzdWIiOiJuaWtvbG92c2tpLm5pa29sYTQyQGdtYWlsLmNvbSIsImV4cCI6MTczOTMyMTM4M30."
                  "g0JZ5WzXTeeXe_Cs7zjalk8QVslLNVEYiSzEZIlqDXE")

    # Build a minimal ASGI scope that includes a "cookie" header with our token.
    # The cookie value is set as "Bearer <token>".
    scope = {
        "type": "http",
        "method": "GET",
        "headers": [
            (b"cookie", f"access_token=Bearer {test_token}".encode("latin-1"))
        ],
    }

    # Create a Request instance from the scope.
    request = Request(scope)

    # Run the get_current_user function in an asyncio event loop.
    try:
        current_user = asyncio.run(get_current_user(request))
        print("User found:", current_user)
    except HTTPException as exc:
        print("HTTPException:", exc.detail)


# @router.get("/auth/google/callback")
# async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
#     try:
#         token = await oauth.google.authorize_access_token(request)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail="OAuth error")
#
#     user_info = token.get('userinfo')
#     if not user_info or not user_info.get("email_verified"):
#         raise HTTPException(status_code=400, detail="Invalid user data")
#
#     email = user_info.email
#     name = user_info.name
#
#     # Check existing user
#     user = db.query(User).filter(User.email == email).first()
#
#     if user and not user.is_google_auth:
#         raise HTTPException(
#             status_code=400,
#             detail="Email already registered with password login"
#         )
#
#     if not user:
#         # Create new Google user
#         user = User(
#             email=email,
#             full_name=name,
#             is_google_auth=True
#         )
#         db.add(user)
#         db.commit()
#
#     # Generate JWT (same as email/password flow)
#     jwt_token = jwt.encode(...)
#
#     response = RedirectResponse(url="/")
#     response.set_cookie(...)  # Same as before
#     return response
