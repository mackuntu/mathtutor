"""Test configuration and fixtures."""

import os
from datetime import datetime, timedelta, timezone

import boto3
import psycopg
import psycopg.conninfo
import pytest
from psycopg import sql
try:
    from moto import mock_dynamodb
except ImportError:
    from moto import mock_aws as mock_dynamodb

from src.auth import AuthManager
from src.database.models import Child, Session, User, Worksheet
from src.database.repository import DynamoDBRepository


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["DYNAMODB_ENDPOINT_URL"] = "http://localhost:8000"


@pytest.fixture(scope="function")
def dynamodb(aws_credentials):
    """Create a mock DynamoDB instance."""
    with mock_dynamodb():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create Users table
        dynamodb.create_table(
            TableName="Users",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create Children table
        dynamodb.create_table(
            TableName="Children",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "parent_email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "ParentEmailIndex",
                    "KeySchema": [{"AttributeName": "parent_email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create Sessions table
        dynamodb.create_table(
            TableName="Sessions",
            KeySchema=[{"AttributeName": "token", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "token", "AttributeType": "S"},
                {"AttributeName": "user_email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "UserEmailIndex",
                    "KeySchema": [{"AttributeName": "user_email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create Worksheets table
        dynamodb.create_table(
            TableName="Worksheets",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "child_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "ChildIdIndex",
                    "KeySchema": [{"AttributeName": "child_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        yield dynamodb


@pytest.fixture(scope="function")
def repository(dynamodb):
    """Create a repository instance with mocked DynamoDB."""
    return DynamoDBRepository()


@pytest.fixture(scope="function")
def auth_manager(repository):
    """Create an auth manager instance."""
    return AuthManager()


@pytest.fixture(scope="function")
def test_user(repository):
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/picture.jpg",
    )
    repository.create_user(user)
    return user


@pytest.fixture(scope="function")
def test_child_dynamodb(repository, test_user):
    """Create a test child in DynamoDB."""
    child = Child(
        parent_email=test_user.email,
        name="Test Child",
        age=8,
        grade=3,
        preferred_color="#FF5733",
    )
    repository.create_child(child)
    return child


@pytest.fixture(scope="function")
def test_worksheet_dynamodb(repository, test_child_dynamodb):
    """Create a test worksheet in DynamoDB."""
    worksheet = Worksheet(
        child_id=test_child_dynamodb.id,
        problems=[
            {"type": "addition", "a": 5, "b": 3},
            {"type": "subtraction", "a": 10, "b": 4},
        ],
    )
    repository.create_worksheet(worksheet)
    return worksheet


@pytest.fixture(scope="function")
def test_session(repository, test_user):
    """Create a test session."""
    session = Session(
        token="test_token",
        user_email=test_user.email,
        expires_at=int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
    )
    repository.create_session(session)
    return session


@pytest.fixture
def sample_problems():
    """Create a list of sample math problems."""
    return [
        "2 + 2",
        "3 - 1",
        "4 × 2",
        "Which number is greater: 12 or 15?",
        "Solve the equation: x + 5 = 10",
        "If you have 3 apples and get 2 more, how many do you have?",
    ]


@pytest.fixture
def cleanup_sessions(repository):
    """Clean up test sessions before each test."""
    # Only clean up sessions with test email addresses
    test_emails = ["test@example.com", "testuser@example.com", "mock@example.com"]

    for email in test_emails:
        try:
            sessions = repository.get_user_sessions(email)
            for session in sessions:
                repository.delete_session(session.token)
        except Exception:
            # Ignore errors if no sessions exist
            pass
    yield


@pytest.fixture
def cleanup_children(repository):
    """Clean up test children before each test."""
    # Only clean up children with test email addresses
    test_emails = ["test@example.com", "testuser@example.com", "mock@example.com"]

    for email in test_emails:
        try:
            children = repository.get_children_by_parent(email)
            for child in children:
                repository.delete_child(child.id)
        except Exception:
            # Ignore errors if user doesn't exist
            pass
    yield


DEFAULT_TEST_DATABASE_URL = "postgresql://postgres:mathtutor@localhost:5432/mathtutor_test"


@pytest.fixture(scope="session")
def pg_url():
    """URL of the Postgres test database, created if missing."""
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    info = psycopg.conninfo.conninfo_to_dict(url)
    dbname = info["dbname"]
    admin_url = psycopg.conninfo.make_conninfo(url, dbname="postgres")
    with psycopg.connect(admin_url, autocommit=True) as admin:
        exists = admin.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)
        ).fetchone()
        if not exists:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    return url


@pytest.fixture
def db(pg_url, monkeypatch):
    """Point the app at the test database with all tables empty."""
    from src.database import db as db_module

    monkeypatch.setenv("DATABASE_URL", pg_url)
    with psycopg.connect(pg_url, autocommit=True) as conn:
        db_module.ensure_schema(conn)
        conn.execute(
            "TRUNCATE users, children, sessions, worksheets, device_tokens CASCADE"
        )
    yield pg_url


@pytest.fixture
def app():
    from src import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()
