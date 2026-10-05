"""
routers/auth_router.py
Authentication endpoints: login, register, profile.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import uuid

from database import get_db
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "Student"


@router.post("/login")
def login(req: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (req.email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    user = dict(row)

    if not user.get("hashed_password"):
        raise HTTPException(status_code=401, detail="Account not properly configured.")

    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
    )
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    }


@router.post("/register")
def register(req: RegisterRequest):
    conn = get_db()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (req.email.strip().lower(),))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    if len(req.password) < 8:
        conn.close()
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    user_id = str(uuid.uuid4())
    hashed = hash_password(req.password)

    cursor.execute(
        "INSERT INTO users (id, name, email, role, hashed_password) VALUES (?, ?, ?, ?, ?)",
        (user_id, req.name.strip(), req.email.strip().lower(), req.role.strip(), hashed),
    )
    conn.commit()
    conn.close()

    token = create_access_token(
        user_id=user_id,
        email=req.email.strip().lower(),
        name=req.name.strip(),
        role=req.role.strip(),
    )
    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": req.name.strip(),
            "email": req.email.strip().lower(),
            "role": req.role.strip(),
        },
    }


@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user)):
    """Return current user info from JWT."""
    return {"user": current_user}
