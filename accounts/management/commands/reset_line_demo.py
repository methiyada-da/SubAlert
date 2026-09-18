from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Reset a user's LINE connection for development or demo use."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Username to reset")

    def handle(self, *args, **options):
        username = options["username"]
        user_model = get_user_model()

        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist as exc:
            raise CommandError(f'User "{username}" was not found.') from exc

        user.line_id = None
        user.line_status = 0
        user.save(update_fields=["line_id", "line_status"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Reset LINE connection for {username} successfully."
            )
        )
