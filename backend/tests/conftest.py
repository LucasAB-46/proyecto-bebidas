# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from model_bakery import baker
from core_app.models import Local


@pytest.fixture(scope="session", autouse=True)
def ensure_locales(django_db_setup, django_db_blocker):
    """Asegura que existan Local(id=1) y Local(id=2) para evitar violaciones de FK en tests."""
    with django_db_blocker.unblock():
        Local.objects.get_or_create(id=1, defaults={"nombre": "Local 1"})
        Local.objects.get_or_create(id=2, defaults={"nombre": "Local 2"})


@pytest.fixture
def anon_client():
    c = APIClient()
    c.credentials(HTTP_X_LOCAL_ID="1")
    return c


@pytest.fixture
def auth_client(db):
    User = get_user_model()
    user = User.objects.filter(username="tester").first()
    if not user:
        user = User.objects.create_user(
            username="tester", email="tester@example.com", password="pass1234"
        )
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_LOCAL_ID="1")
    return client
