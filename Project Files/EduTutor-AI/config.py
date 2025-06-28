import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

JWT_SECRET = st.secrets["JWT_SECRET"]
JWT_ALGORITHM = st.secrets["JWT_ALGORITHM"] 