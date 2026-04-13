"""
Cria ou actualiza um utilizador de desenvolvimento com e-mail allauth verificado.

Só corre com DJANGO_DEBUG=True (evita uso acidental em produção).
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = "Cria/atualiza utilizador de teste (DEBUG=True apenas)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default="teste@rid.localhost",
            help="E-mail do utilizador (default: teste@rid.localhost)",
        )
        parser.add_argument(
            "--password",
            default="RidTeste123!",
            help="Palavra-passe em texto claro (default: RidTeste123!)",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Este comando só está disponível com DJANGO_DEBUG=True.")

        email = (options["email"] or "").strip().lower()
        password = options["password"]
        if not email:
            raise CommandError("E-mail vazio.")
        if not password:
            raise CommandError("Palavra-passe vazia.")

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            base = email.split("@", 1)[0].replace(".", "_")[:30] or "ridtest"
            username = f"{base}_{uuid.uuid4().hex[:8]}"
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f"Criado utilizador novo: {email}"))
        else:
            user.set_password(password)
            user.is_active = True
            user.save(update_fields=["password", "is_active"])
            self.stdout.write(
                self.style.WARNING(f"Actualizado utilizador existente: {email}")
            )

        EmailAddress.objects.filter(user=user).update(primary=False)
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True},
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Login allauth OK. E-mail: {email}  |  Palavra-passe: (a que definiste com --password)"
            )
        )
        self.stdout.write(
            "Em /accounts/login/ usa o e-mail completo no campo de login."
        )
