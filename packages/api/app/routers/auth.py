from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.core import rate_limit
from app.core.logging import get_logger
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, UserUpdate, PasswordChange
from app.services.auth_service import register_user, login_user
from app.core.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

logger = get_logger("app.auth")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(rate_limit.register_ip_limiter)],
)
def register(data: UserRegister, request: Request, db: Session = Depends(get_db)):
    user = register_user(data, db)
    logger.info(
        "user registered",
        extra={"registered_user_id": str(user.id), "client_ip": rate_limit.client_identity(request)},
    )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit.login_ip_limiter)],
)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    # Two budgets guard this endpoint. The IP limit (applied as a dependency
    # above) stops one host spraying many accounts; this per-account limit stops
    # a distributed attempt from spraying one account from many hosts.
    rate_limit.login_account_limiter.check_identity(data.email.lower())

    try:
        token = login_user(data, db)
    except HTTPException:
        # Deliberately no email in the log message body — the structured field
        # is enough to correlate, and log lines get shipped off-box.
        logger.warning(
            "login failed",
            extra={"client_ip": rate_limit.client_identity(request), "email_attempted": data.email},
        )
        raise

    logger.info("login succeeded", extra={"client_ip": rate_limit.client_identity(request)})
    return {"access_token": token}


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if data.email and data.email != current_user.email:
        from app.models.user import User
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = data.email
    if data.full_name is not None:
        current_user.full_name = data.full_name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put(
    "/me/password",
    status_code=204,
    dependencies=[Depends(rate_limit.password_change_limiter)],
)
def change_password(data: PasswordChange, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Rate limited for the same reason as login: this endpoint also verifies a
    # password, so it is an oracle for guessing one.
    if not verify_password(data.current_password, current_user.hashed_password):
        logger.warning("password change rejected", extra={"reason": "wrong_current_password"})
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    logger.info("password changed")
