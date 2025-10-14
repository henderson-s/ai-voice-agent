from fastapi import APIRouter, Depends, HTTPException, status
from backend.models.auth import UserRegister, UserLogin, Token, UserResponse
from backend.database import Database, get_db
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Database = Depends(get_db)):
    try:
        response = db.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {"full_name": user_data.full_name}
            }
        })
        
        if not response.session:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed")
        
        return Token(access_token=response.session.access_token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Database = Depends(get_db)):
    try:
        response = db.client.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not response.session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        return Token(access_token=response.session.access_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.user_metadata.get("full_name", "")
    )

