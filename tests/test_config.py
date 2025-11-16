from core.config import Config


def test_sqlalchemy_database_uri_builds_expected_connection_string():
    config = Config(
        SECRET_KEY="secret",
        POSTGRES_USER="skyflow",
        POSTGRES_PASSWORD="pass123",
        POSTGRES_HOST="db.example.com",
        POSTGRES_DB="videoproducer",
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="adminpass",
    )

    assert (
        str(config.SQLALCHEMY_DATABASE_URI)
        == "postgresql+asyncpg://skyflow:pass123@db.example.com:5432/videoproducer"
    )
