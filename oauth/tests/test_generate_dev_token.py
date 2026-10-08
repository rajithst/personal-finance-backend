import io
import pytest
from django.core.management import call_command
from oauth.models import User


@pytest.mark.django_db
class TestGenerateDevTokenCommand:
    def test_generate_dev_token_success(self):
        user, _ = User.objects.get_or_create(id=1, defaults={"username": "devuser", "email": "devuser@example.com"})
        out = io.StringIO()
        call_command("generate_dev_token", user_id=user.id, days=30, stdout=out)
        output = out.getvalue()
        assert "Generated JWT token" in output
        assert "Token:" in output
        assert "Days valid: 30" in output

    def test_generate_dev_token_user_not_found(self):
        from django.core.management.base import CommandError
        with pytest.raises(CommandError):
            call_command("generate_dev_token", user_id=999999)
