from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from jose import jwt
from dotenv import load_dotenv
import os
import bcrypt
from services.pinecone_service import index
from passlib.hash import bcrypt  # ✅ use passlib's bcrypt
import streamlit as st


load_dotenv()
router = APIRouter()

SECRET_KEY = st.secrets["JWT_SECRET"]
ALGORITHM = st.secrets["JWT_ALGORITHM"]

@router.post("/auth/email")
async def login_email(
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        # Search for the email in Pinecone by filtering metadata
        response = index.query(
            vector=[0.0] * 1024,
            top_k=1000,
            include_metadata=True,
            filter={
                "$and": [
                    {"email": {"$eq": email}},     # email should be a string
                    {"type": {"$eq": "user"}}      # type should also be a string
                ]
            }
)

        if not response.matches:
            print("❌ User not found.")
            return RedirectResponse("/login", status_code=303)

        user_data = response.matches[0].metadata
        hashed_pw = user_data.get("password")
        role = user_data.get("role", "student")

        print("Entered password:", password)
        print("Hashed password from DB:", hashed_pw)
        result = bcrypt.verify(password, hashed_pw)
        print("Password match result:", result)

        if not bcrypt.verify(password, hashed_pw):
            print("❌ Password does not match.")
            return RedirectResponse("/login", status_code=303)

        # ✅ Issue JWT
        token_data = {"sub": email, "role": role, "name": user_data.get("name", "")}
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        if role == "educator":
            return RedirectResponse(url=f"/dashboard/educator?token={token}", status_code=303)
        else:
            return RedirectResponse(url=f"/dashboard/student?token={token}", status_code=303)


    except Exception as e:
        print("❌ Login error:", str(e))
        return RedirectResponse("/login", status_code=303) 