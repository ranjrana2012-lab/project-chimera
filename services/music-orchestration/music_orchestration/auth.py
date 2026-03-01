import os
from typing import Callable
from jwt import decode, InvalidTokenError
from fastapi import HTTPException, status
from music_orchestration.schemas import Role, UserContext


class PermissionChecker:
    """Role-based permission checking"""

    PERMISSIONS = {
        Role.SOCIAL_MEDIA_USER: [
            "music:generate",
            "music:use_marketing",
            "music:view_own"
        ],
        Role.SHOW_OPERATOR: [
            "music:generate",
            "music:approve_show",
            "music:use_show",
            "music:view_all"
        ],
        Role.DEVELOPER: [
            "music:generate",
            "music:manage_models",
            "music:view_all",
            "music:clear_cache"
        ],
        Role.ADMIN: ["*"]
    }

    @classmethod
    def check_permission(cls, user: UserContext, permission: str) -> bool:
        """Check if user has permission"""
        user_permissions = cls.PERMISSIONS.get(user.role, [])

        # Admin has all permissions
        if "*" in user_permissions:
            return True

        return permission in user_permissions

    @classmethod
    def require_permission(cls, permission: str) -> Callable[[UserContext], None]:
        """Return a function that checks permission and raises if missing"""
        def check(user: UserContext) -> None:
            if not cls.check_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
        return check


class ServiceAuthenticator:
    """JWT-based service authentication"""

    def __init__(self, secret_key: str | None = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET", "dev-secret")
        self.algorithm = "HS256"

    def validate_token(self, token: str) -> UserContext:
        """Validate JWT token and return user context"""
        try:
            payload = decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return UserContext(
                service_name=payload["sub"],
                role=Role(payload["role"]),
                permissions=payload.get("permissions", [])
            )
        except InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except KeyError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token payload: missing {e}"
            )
