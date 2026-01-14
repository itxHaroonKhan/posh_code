"""
Authentication router with signup and signin endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from contextlib import contextmanager

from ..database import engine, get_session
from ..models.user import User
from ..schemas.auth import SignupRequest, SigninRequest, TokenResponse, ErrorResponse
from ..services import auth_service


router = APIRouter()


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "User created successfully",
            "model": TokenResponse
        },
        400: {
            "description": "Bad request (invalid data or email already exists)",
            "model": ErrorResponse
        },
        422: {
            "description": "Validation error (invalid email format or weak password)",
            "model": ErrorResponse
        }
    },
    summary="Register a new user",
    description="Create a new user account with email and password. Returns JWT token for immediate authentication."
)
def signup(
    request: SignupRequest,
    session: Session = Depends(get_session)
):
    """
    Register a new user account.

    - **email**: Valid email address (unique)
    - **password**: Password meeting strength requirements (min 8 chars, uppercase, lowercase, digit)

    Returns JWT token for immediate authentication after signup.
    """
    # Check if email already exists
    statement = select(User).where(User.email == request.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Bad Request",
                "message": "Email already exists",
                "detail": f"User with email {request.email} is already registered"
            }
        )

    # Hash password
    password_hash = auth_service.hash_password(request.password)

    # Create new user
    new_user = User(
        email=request.email,
        password_hash=password_hash
    )

    # Save to database
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Generate JWT token
    token = auth_service.create_jwt_token(new_user.id, new_user.email)

    return TokenResponse(
        user_id=str(new_user.id),
        email=new_user.email,
        token=token
    )


@router.post(
    "/signin",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Signin successful",
            "model": TokenResponse
        },
        401: {
            "description": "Unauthorized (invalid credentials)",
            "model": ErrorResponse
        },
        422: {
            "description": "Validation error (invalid email format)",
            "model": ErrorResponse
        }
    },
    summary="Sign in existing user",
    description="Authenticate with email and password. Returns JWT token on success."
)
def signin(
    request: SigninRequest,
    session: Session = Depends(get_session)
):
    """
    Sign in an existing user.

    - **email**: User's registered email address
    - **password**: User's password

    Returns JWT token for authenticated API requests.
    """
    # Find user by email
    statement = select(User).where(User.email == request.email)
    user = session.exec(statement).first()

    # Verify user exists and password is correct
    if not user or not auth_service.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "message": "Invalid credentials",
                "detail": "Email or password is incorrect"
            }
        )

    # Generate JWT token
    token = auth_service.create_jwt_token(user.id, user.email)

    return TokenResponse(
        user_id=str(user.id),
        email=user.email,
        token=token
    )
