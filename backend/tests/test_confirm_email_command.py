"""Comando confirm_email — marca EmailAddress allauth como verificado."""

from __future__ import annotations

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_confirm_email_marks_verified() -> None:
    User = get_user_model()
    user = User.objects.create_user(
        username="cuser",
        email="confirm-me@example.com",
        password="x",
    )
    EmailAddress.objects.create(
        user=user,
        email=user.email,
        verified=False,
        primary=True,
    )

    call_command("confirm_email", "confirm-me@example.com")

    ea = EmailAddress.objects.get(user=user, email__iexact=user.email)
    assert ea.verified is True
    assert ea.primary is True


@pytest.mark.django_db
def test_confirm_email_unknown_user() -> None:
    with pytest.raises(CommandError, match="não encontrado"):
        call_command("confirm_email", "nobody@example.com")
