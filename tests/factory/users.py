from faker import Faker

from app.models import Role

fake = Faker()


def create_fake_user():
    username = fake.user_name()
    password = fake.password(length=12)
    role = Role.USER

    return {
        "username": username,
        "password": password,
        "role": role.value,
    }
