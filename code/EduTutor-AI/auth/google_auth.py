# backend/auth/google_auth.py

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from jose import jwt
import os
from dotenv import load_dotenv
from config import JWT_SECRET, JWT_ALGORITHM
# from auth.google_oauth_config import oauth  # Google OAuth setup not implemented here
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
import urllib.parse
from services.pinecone_service import get_user_by_email, upsert_user_data
import uuid

# NOTE: Google OAuth setup is not implemented in this file. You need to configure OAuth separately if required.

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET", "devsecret")  # Add in .env later
ALGORITHM = "HS256"

router = APIRouter()

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

# The following endpoints require a configured OAuth object, which is not present.
# You need to implement Google OAuth setup if you want to use these endpoints.
# @router.get("/auth/google")
# async def login_via_google(request: Request):
#     redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
#     return await oauth.google.authorize_redirect(request, redirect_uri)
# @router.get("/auth/google/callback")
# async def google_callback(request: Request):
#     ...

# @router.get("/auth/google")
# async def login_via_google(request: Request):
#     redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
#     return await oauth.google.authorize_redirect(request, redirect_uri)
#
# @router.get("/auth/google/callback")
# async def google_callback(request: Request):
#     try:
#         token = await oauth.google.authorize_access_token(request)
#         print("✅ Token received:", token)
#         print('line 39')
#         for key in token:
#                 print(f"{key}: {type(token[key])}")
#         id_token = token.get("id_token")
#         print(f"id token:{id_token}")
#
#         user = google_id_token.verify_oauth2_token(
#             id_token,
#             google_requests.Request(),
#             audience=os.getenv("GOOGLE_CLIENT_ID")  # Replace with your actual client ID
#         )
#
#         print("User Info:", user)
#         print("✅ User info:", user)
#         print('line 43')
#         email = user.get("email")
#         name = user.get("name")
#         picture = user.get("picture")
#
#         if not email:
#             print("❌ Email not found in Google user object.")
#             return RedirectResponse("/login")
#
#         # Assign default role
#         role = "student"
#         print('line 54')
#
#         existing_user = get_user_by_email(email)
#         if not existing_user:
#             user_id = str(uuid.uuid4())
#             user_data = {
#                 "email": email,
#                 "password": "google_oauth",
#                 "role": role,
#                 "name": name,
#                 "picture": picture
#             }
#             upsert_user_data(user_id, user_data)
#         # Encode your own app-level JWT for session
#         token_data = {"sub": email, "name": name, "role": role}
#         jwt_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
#         encoded_token = urllib.parse.quote(jwt_token)
#         print('line 58')
#         url = f"/dashboard/student?token={encoded_token}"
#         return RedirectResponse(url=url, status_code=303)
#
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         print(f"❌ Google OAuth Callback Error: srt{e}")
#         return RedirectResponse("/login") 