from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import hashlib
from typing import Optional
import sqlite3

app = FastAPI()

# CORS settings remain unchanged
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"

DATABASE_FILE = "my_database.db"

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

def create_table():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  created_at TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def load_database():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    users = []
    for row in rows:
        users.append({
            "id": row[0],
            "username": row[1],
            "password": row[2],
            "created_at": datetime.fromisoformat(row[3]),
        })
    conn.close()
    return users

def save_user(user):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users (username, password, created_at)
                 VALUES (?, ?, ?)''', (user["username"], user["password"], user["created_at"]))
    conn.commit()
    conn.close()

@app.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    create_table()  # Create table if it doesn't exist
    users = load_database()

    if any(u["username"] == user.username for u in users):
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = {
        "id": None,
        "username": user.username,
        "password": hash_password(user.password),
        "created_at": datetime.utcnow().isoformat(),
    }

    save_user(new_user)

    # Get the newly created user's id (SQLite auto-increments)
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT last_insert_rowid()")
    new_user["id"] = c.fetchone()[0]
    conn.close()

    return UserOut(
        id=new_user["id"],
        username=new_user["username"],
        created_at=datetime.fromisoformat(new_user["created_at"]),
    )

@app.post("/login")
async def login(user: UserCreate):
    users = load_database()

    # Find the user in the database
    db_user = next((u for u in users if u["username"] == user.username), None)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_token(db_user["id"])
    return {"token": token, "success": True}

@app.get("/me", response_model=UserOut)
async def me(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if " " not in authorization:
        raise HTTPException(status_code=400, detail="Authorization header is malformed")

    token = authorization.split(" ")[1]
    try:
        user_id = verify_token(token)
    except HTTPException as e:
        raise e

    users = load_database()

    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return UserOut(
        id=user["id"],
        username=user["username"],
        created_at=datetime.fromisoformat(user["created_at"]),
    )

if __name__ == "__main__":
    import uvicorn

    create_table()
    uvicorn.run(app, host="127.0.0.1", port=8001)
