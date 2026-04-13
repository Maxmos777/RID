"""create_dev_user — só em DEBUG."""

from __future__ import annotations

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_create_dev_user_blocked_without_debug(settings) -> None:
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG"):
        call_command("create_dev_user")


@pytest.mark.django_db
def test_create_dev_user_creates_verified_user(settings) -> None:
    settings.DEBUG = True
    call_command(
        "create_dev_user",
        email="riddev_create@test.example",
        password="SecretPass9",
    )
    User = get_user_model()
    u = User.objects.get(email__iexact="riddev_create@test.example")
    assert u.check_password("SecretPass9")
    ea = EmailAddress.objects.get(user=u, email__iexact=u.email)
    assert ea.verified and ea.primary
