from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserResponse
from app.schemas.user import UserCreate
from app.services.github_oauth import GitHubOAuthService
from app.utils.jwt import create_access_token
from app.api.dependencies import get_current_user
import secrets

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# temp tokens, TODO: in prod use redis or something similar
oauth_states = set()

@router.get("/login")
async def login():
    """Initiate GitHub OAuth login"""
    state = secrets.token_urlsafe(32)
    oauth_states.add(state)

    authorization_url = GitHubOAuthService.get_authorization_url(state)

    return {
        "authorization_url": authorization_url,
        "state": state
    }

@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle GitHub OAuth callback"""
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    oauth_states.remove(state)

    github_token = await GitHubOAuthService.exchange_code_for_tokem(code)
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
    
    github_user = await GitHubOAuthService.get_user_info(github_token)
    if not github_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch user information"
        )
    
    result = await db.execute(select(User).where(User.github_id == github_user.id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            github_id=github_user.id,
            username=github_user.login,
            email=github_user.email,
            github_token=github_token,
        )
        db.add(user)
    else:
        user.github_token = github_token
        user.email = github_user.email
    
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(
        data={"user_id": user.id, "github_id": user.github_id}
    )

    return Token(acces_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user