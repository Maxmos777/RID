from __future__ import annotations

from django.contrib import admin

from .models import TenantUser


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ("email", "langflow_user_id", "langflow_api_key", "is_active")
    search_fields = ("email", "langflow_user_id")
    readonly_fields = ()

