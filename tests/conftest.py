"""Test configuration and fixtures."""

import os
from datetime import datetime, timedelta, timezone

import boto3
import pytest
from moto import mock_dynamodb

from src.auth import AuthManager
from src.database.models import Child, Session, User, Worksheet
from src.database.repository import DynamoDBRepository
from src.document.renderer import DocumentRenderer


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


@pytest.fixture(scope="function")
def renderer():
    """Create a document renderer instance."""
    return DocumentRenderer()


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


@pytest.fixture(autouse=True)
def cleanup_sessions(repository):
    """Clean up all sessions before each test."""
    # Get all sessions and delete them
    sessions = repository.scan_sessions()
    for session in sessions:
        repository.delete_session(session.token)
    yield


@pytest.fixture(autouse=True)
def cleanup_children(repository):
    """Clean up all children before each test."""
    # Get all children and delete them
    children = repository.scan_children()
    for child in children:
        repository.delete_child(child.id)
    yield
