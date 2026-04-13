"""
Marca o EmailAddress do django-allauth como verificado (dev / operações).

Útil quando EMAIL_BACKEND é consola ou SMTP falhou e precisas de desbloquear o login
com ACCOUNT_EMAIL_VERIFICATION = mandatory.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "Marca o e-mail do utilizador como confirmado no allauth."

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="E-mail exactamente como no registo (case-insensitive).",
        )

    def handle(self, *args, **options):
        raw = options["email"].strip()
        if not raw:
            raise CommandError("E-mail vazio.")

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=raw)
        except User.DoesNotExist as e:
            raise CommandError(f"Utilizador com e-mail «{raw}» não encontrado.") from e

        canonical = (user.email or raw).strip().lower()

        ea, created = EmailAddress.objects.get_or_create(
            user=user,
            email=canonical,
            defaults={"verified": True, "primary": True},
        )
        if not created:
            EmailAddress.objects.filter(user=user).update(primary=False)
            ea.verified = True
            ea.primary = True
            ea.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"E-mail «{canonical}» marcado como verificado e principal (user pk={user.pk})."
            )
        )
