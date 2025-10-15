from fastapi import APIRouter, Depends, HTTPException, status
import logging
from backend.models.auth import UserRegister, UserLogin, Token, UserResponse, RegistrationResponse
from backend.database import Database, get_db
from backend.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Database = Depends(get_db)):
    logger.info(f"Registration attempt for email: {user_data.email}")
    try:
        logger.debug(f"Calling Supabase sign_up for: {user_data.email}")
        response = db.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {"full_name": user_data.full_name}
            }
        })
        
        logger.debug(f"Supabase response user: {response.user}")
        logger.debug(f"Supabase response session: {response.session}")
        
        # Check if user was created successfully
        if not response.user:
            logger.error(f"Registration failed - no user returned for: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Registration failed - user creation error"
            )
        
        # Check if email confirmation is required
        if not response.session:
            logger.info(f"Registration successful for {user_data.email} - email confirmation required")
            return RegistrationResponse(
                message="Registration successful! Please check your email to confirm your account.",
                email=user_data.email,
                requires_confirmation=True,
                access_token=None
            )
        
        # Email confirmation disabled - user can login immediately
        logger.info(f"Registration successful for: {user_data.email} - auto-confirmed")
        return RegistrationResponse(
            message="Registration successful! You can now login.",
            email=user_data.email,
            requires_confirmation=False,
            access_token=response.session.access_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error for {user_data.email}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Registration failed: {str(e)}")


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Database = Depends(get_db)):
    logger.info(f"Login attempt for email: {credentials.email}")
    try:
        logger.debug(f"Calling Supabase sign_in_with_password for: {credentials.email}")
        response = db.client.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        logger.debug(f"Supabase login response: {response}")
        
        if not response.session:
            logger.warning(f"Login failed - no session for: {credentials.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        logger.info(f"Login successful for: {credentials.email}")
        return Token(access_token=response.session.access_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {credentials.email}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.user_metadata.get("full_name", "")
    )

