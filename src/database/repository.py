"""Repository class for DynamoDB operations."""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3

from .config import (
    CHILD_ID_INDEX,
    CHILDREN_TABLE,
    PARENT_EMAIL_INDEX,
    SESSION_TTL_ATTRIBUTE,
    SESSIONS_TABLE,
    USER_EMAIL_INDEX,
    USERS_TABLE,
    WORKSHEETS_TABLE,
)
from .models import Child, Session, User, Worksheet


class DynamoDBRepository:
    """Repository class for DynamoDB operations."""

    def __init__(self):
        """Initialize DynamoDB client."""
        # Use local endpoint in development mode
        endpoint_url = (
            "http://localhost:8000" if os.getenv("FLASK_ENV") == "development" else None
        )

        self.dynamodb = boto3.client(
            "dynamodb",
            endpoint_url=endpoint_url,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "testing"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "testing"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

    # User operations
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        response = self.dynamodb.get_item(
            TableName=USERS_TABLE, Key={"email": {"S": email}}
        )
        return User.from_item(response.get("Item"))

    def create_user(self, user: User) -> None:
        """Create a new user."""
        self.dynamodb.put_item(TableName=USERS_TABLE, Item=user.to_item())

    def update_user(self, user: User) -> None:
        """Update an existing user."""
        user.updated_at = user.utc_now()
        self.dynamodb.put_item(TableName=USERS_TABLE, Item=user.to_item())

    # Child operations
    def get_child_by_id(self, child_id: str) -> Optional[Child]:
        """Get child by ID."""
        response = self.dynamodb.get_item(
            TableName=CHILDREN_TABLE, Key={"id": {"S": child_id}}
        )
        return Child.from_item(response.get("Item"))

    def get_children_by_parent(self, parent_email: str) -> List[Child]:
        """Get all children for a parent."""
        response = self.dynamodb.query(
            TableName=CHILDREN_TABLE,
            IndexName=PARENT_EMAIL_INDEX,
            KeyConditionExpression="parent_email = :email",
            ExpressionAttributeValues={":email": {"S": parent_email}},
        )
        return [Child.from_item(item) for item in response.get("Items", [])]

    def create_child(self, child: Child) -> None:
        """Create a new child."""
        self.dynamodb.put_item(TableName=CHILDREN_TABLE, Item=child.to_item())

    def update_child(self, child: Child) -> None:
        """Update an existing child."""
        child.updated_at = child.utc_now()
        self.dynamodb.put_item(TableName=CHILDREN_TABLE, Item=child.to_item())

    def delete_child(self, child_id: str) -> None:
        """Delete a child."""
        self.dynamodb.delete_item(TableName=CHILDREN_TABLE, Key={"id": {"S": child_id}})

    def scan_children(self) -> List[Child]:
        """Scan all children."""
        response = self.dynamodb.scan(TableName=CHILDREN_TABLE)
        return [Child.from_item(item) for item in response.get("Items", [])]

    # Session operations
    def get_session(self, token: str) -> Optional[Session]:
        """Get session by token."""
        response = self.dynamodb.get_item(
            TableName=SESSIONS_TABLE, Key={"token": {"S": token}}
        )
        return Session.from_item(response.get("Item"))

    def get_user_sessions(self, user_email: str) -> List[Session]:
        """Get all sessions for a user."""
        response = self.dynamodb.query(
            TableName=SESSIONS_TABLE,
            IndexName=USER_EMAIL_INDEX,
            KeyConditionExpression="user_email = :email",
            ExpressionAttributeValues={":email": {"S": user_email}},
        )
        return [Session.from_item(item) for item in response.get("Items", [])]

    def create_session(self, session: Session) -> None:
        """Create a new session."""
        self.dynamodb.put_item(TableName=SESSIONS_TABLE, Item=session.to_item())

    def delete_session(self, token: str) -> None:
        """Delete a session."""
        self.dynamodb.delete_item(TableName=SESSIONS_TABLE, Key={"token": {"S": token}})

    def scan_sessions(self) -> List[Session]:
        """Scan all sessions."""
        response = self.dynamodb.scan(TableName=SESSIONS_TABLE)
        return [Session.from_item(item) for item in response.get("Items", [])]

    # Worksheet operations
    def get_worksheet(self, worksheet_id: str) -> Optional[Worksheet]:
        """Get worksheet by ID."""
        response = self.dynamodb.get_item(
            TableName=WORKSHEETS_TABLE, Key={"id": {"S": worksheet_id}}
        )
        return Worksheet.from_item(response.get("Item"))

    def get_child_worksheets(self, child_id: str) -> List[Worksheet]:
        """Get all worksheets for a child."""
        response = self.dynamodb.query(
            TableName=WORKSHEETS_TABLE,
            IndexName=CHILD_ID_INDEX,
            KeyConditionExpression="child_id = :child_id",
            ExpressionAttributeValues={":child_id": {"S": child_id}},
        )
        return [Worksheet.from_item(item) for item in response.get("Items", [])]

    def create_worksheet(self, worksheet: Worksheet) -> None:
        """Create a new worksheet."""
        self.dynamodb.put_item(TableName=WORKSHEETS_TABLE, Item=worksheet.to_item())

    def update_worksheet(self, worksheet: Worksheet) -> None:
        """Update an existing worksheet."""
        worksheet.updated_at = worksheet.utc_now()
        self.dynamodb.put_item(TableName=WORKSHEETS_TABLE, Item=worksheet.to_item())

    def delete_worksheet(self, worksheet_id: str) -> None:
        """Delete a worksheet."""
        self.dynamodb.delete_item(
            TableName=WORKSHEETS_TABLE, Key={"id": {"S": worksheet_id}}
        )


_repository_instance = None


def get_repository() -> DynamoDBRepository:
    """Get or create a DynamoDBRepository instance."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = DynamoDBRepository()
    return _repository_instance
