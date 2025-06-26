import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from passlib.hash import bcrypt

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Load environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is not set. Please check your .env file.")

# Define a non-zero dummy vector
SAFE_DUMMY_VECTOR = [1e-6] + [0.0] * 1023  # Length = 1024

# Initialize Pinecone client with API key
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1024,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-west-2")
    )

# Access the index
index = pc.Index(PINECONE_INDEX_NAME)

# === USER AUTH DATA ===

def upsert_user_data(user_id: str, user_data: dict):
    """Store user login/signup data with safe dummy vector and hashed password."""
    metadata = {
        "type": "user",
        "email": user_data["email"],
        "password": user_data["password"],
        "role": user_data["role"]
    }
    index.upsert(vectors=[
        {
            "id": user_id,
            "values": SAFE_DUMMY_VECTOR,
            "metadata": metadata
        }
    ])

def get_user_by_email(email: str):
    """Retrieve user by email."""
    results = index.query(
        vector=SAFE_DUMMY_VECTOR,
        top_k=1,
        filter={
            "type": "user",
            "email": {"$eq": email}
        },
        include_metadata=True
    )
    if results and results.matches:
        return results.matches[0].metadata
    return None

# === QUIZ RESULT DATA ===

def store_quiz_result(student_email: str, quiz_data: dict):
    print("📥 Storing quiz for:", student_email)
    """Store quiz result for a student."""
    metadata = {
        "type": "quiz",
        "email": student_email,
        "topic": quiz_data["topic"],
        "score": quiz_data["score"],
        "total": quiz_data["total"], 
        "time": quiz_data["time"]  # Format: 'YYYY-MM-DD HH:MM:SS'
    }
    quiz_id = f"{student_email}_{quiz_data['time']}"
    index.upsert(vectors=[
        {
            "id": quiz_id,
            "values": SAFE_DUMMY_VECTOR,
            "metadata": metadata
        }
    ])

def get_all_quiz_results():
    """Return all quiz entries (for educators)."""
    results = index.query(
        vector=SAFE_DUMMY_VECTOR,
        top_k=1000,
        include_metadata=True,
        filter={"type": "quiz"}
    )
    return [match.metadata for match in results.matches]

def get_quizzes_by_student(email: str):
    results = index.query(
        vector=SAFE_DUMMY_VECTOR,
        top_k=100,
        filter={
            "type": "quiz",
            "email": {"$eq": email}
        },
        include_metadata=True
    )
    return [match.metadata for match in results.matches] 