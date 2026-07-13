import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create a default superuser if none exists (for Docker bootstrap)"

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("Superuser already exists — skipping."))
            return

        email = os.environ.get("ADMIN_EMAIL", "admin@localhost")
        password = os.environ.get("ADMIN_PASSWORD", "")
        env_type = os.environ.get("ENV_TYPE", "dev")

        if not password:
            if env_type == "prod":
                self.stderr.write(
                    self.style.ERROR(
                        "ADMIN_PASSWORD is not set and ENV_TYPE=prod — refusing to "
                        "create a superuser with a guessable default password. Set "
                        "ADMIN_PASSWORD to a real secret and redeploy."
                    )
                )
                return
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: ADMIN_PASSWORD not set — using default 'admin'. "
                    "This is only acceptable outside production."
                )
            )
            password = "admin"

        User.objects.create_superuser(
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Created default superuser: {email}"))
