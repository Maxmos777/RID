from __future__ import annotations

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

__all__ = ["TenantUser", "TenantMembership"]


class TenantUser(AbstractUser):
    """
    Custom user model stored in the shared (public) schema.
    Langflow integration fields stored per-user.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    langflow_user_id = models.UUIDField(null=True, blank=True, unique=True)
    # API key — never expose via serializers; encrypt at rest before production
    langflow_api_key = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        app_label = "accounts"

    def __str__(self) -> str:
        return self.email or self.username


class TenantMembership(models.Model):
    """
    Links a TenantUser to a Customer (tenant).
    A user can belong to multiple tenants with different roles.

    invited_by
    ----------
    FK para a TenantMembership de quem enviou o convite.
    Captura tanto quem convidou (.invited_by.user) como em que
    capacidade (.invited_by.role). SET_NULL preserva o histórico
    se o convidador sair do tenant.
    Atalho: membership.invited_by_user -> o TenantUser convidador.
    """

    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("member", "Member"),
        ("viewer", "Viewer"),
    ]

    user = models.ForeignKey(
        TenantUser,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    # Store schema_name instead of FK to avoid cross-schema joins
    tenant_schema = models.CharField(max_length=63, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invites",  # membership.sent_invites.all() -> convites enviados
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "accounts"
        unique_together = [("user", "tenant_schema")]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.tenant_schema} ({self.role})"

    @property
    def invited_by_user(self) -> "TenantUser | None":
        """Retorna o TenantUser que enviou o convite (atalho para invited_by.user)."""
        return self.invited_by.user if self.invited_by_id else None
