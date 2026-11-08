import os

import pytest
from sqlalchemy import text

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def postgres_app():
    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    class PostgreSQLTestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = database_url
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    app = create_app(PostgreSQLTestConfig)

    with app.app_context():
        # Verify that this is PostgreSQL and the migrations have been applied.
        dialect = db.engine.dialect.name
        if dialect != "postgresql":
            pytest.fail("Integration tests require PostgreSQL")

        constraint = db.session.execute(
            text("""
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'no_overlapping_confirmed_bookings'
            """)
        ).scalar()

        if not constraint:
            pytest.fail("PostgreSQL overlap constraint is missing")

        yield app

        db.session.remove()


@pytest.fixture
def postgres_client(postgres_app):
    return postgres_app.test_client()
