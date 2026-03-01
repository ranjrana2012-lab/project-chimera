import pytest
from unittest.mock import Mock

from music_orchestration.auth import PermissionChecker, ServiceAuthenticator
from music_orchestration.schemas import Role, UserContext


def test_permission_checker_social_media_user():
    user = UserContext(
        service_name="social_media",
        role=Role.SOCIAL_MEDIA_USER,
        permissions=["music:generate", "music:use_marketing"]
    )

    assert PermissionChecker.check_permission(user, "music:generate") is True
    assert PermissionChecker.check_permission(user, "music:approve_show") is False


def test_permission_checker_show_operator():
    user = UserContext(
        service_name="operator_console",
        role=Role.SHOW_OPERATOR,
        permissions=["music:generate", "music:approve_show"]
    )

    assert PermissionChecker.check_permission(user, "music:approve_show") is True
    assert PermissionChecker.check_permission(user, "music:manage_models") is False


def test_permission_checker_admin():
    user = UserContext(
        service_name="admin",
        role=Role.ADMIN,
        permissions=["*"]
    )

    assert PermissionChecker.check_permission(user, "music:anything") is True
