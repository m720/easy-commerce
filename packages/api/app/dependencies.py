from typing import Generator, Optional
from fastapi import Depends, HTTPException, Request, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.base import SessionLocal, ReadSessionLocal
from app.core.security import decode_token
from app.core.enums import UserRole
from app.services.audit_service import AuditContext

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_read_db(primary: Session = Depends(get_db)) -> Generator:
    """Session for read-only endpoints that tolerate replication lag.

    Falls back to the primary session when no replica is configured, so the
    same endpoint code works in every environment. Taking the primary as a
    dependency (rather than calling ``SessionLocal`` directly) keeps test
    overrides of ``get_db`` effective for read paths too.

    Do not use this for read-your-own-write flows — an order confirmation read
    immediately after checkout must see the primary.
    """
    if ReadSessionLocal is None:
        yield primary
        return

    replica = ReadSessionLocal()
    try:
        yield replica
    finally:
        replica.close()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    from app.models.user import User

    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def admin_audit(request: Request, current_user=Depends(require_admin)) -> AuditContext:
    """Admin guard that also carries the audit actor.

    Endpoints depend on this instead of ``require_admin`` when they mutate
    state: it enforces the role *and* hands back the context needed to record
    who did it, from where.
    """
    client_ip = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    return AuditContext(actor=current_user, ip_address=client_ip)


class Pagination:
    def __init__(
        self,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ):
        self.skip = skip
        self.limit = limit
