from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand, CommandError
from oauth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class Command(BaseCommand):
    help = "Generate a long-lived JWT Bearer token for development or testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            default=1,
            help="User ID to generate token for (default: 1)",
        )
        parser.add_argument(
            "--username",
            type=str,
            default=None,
            help="Username to generate token for (overrides user-id)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=3650,
            help="Number of days the access token should remain valid (default: 3650 / 10 years)",
        )

    def handle(self, *args, **options):
        username = options.get("username")
        user_id = options.get("user_id")
        days = options.get("days")

        try:
            if username:
                user = User.objects.get(username=username)
            else:
                user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CommandError(f"User not found (user_id={user_id}, username={username})")

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        access.set_exp(lifetime=timedelta(days=days))

        exp_timestamp = access.payload["exp"]
        exp_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        self.stdout.write(self.style.SUCCESS(f"Generated JWT token for user '{user.username}' (ID: {user.id})"))
        self.stdout.write(f"Expires at (UTC): {exp_dt.isoformat()}")
        self.stdout.write(f"Days valid: {days}")
        self.stdout.write("\nToken:")
        self.stdout.write(str(access))
