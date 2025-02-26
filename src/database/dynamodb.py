"""DynamoDB data access layer."""

import os
from datetime import datetime
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key

from ..models.dynamodb import (
    CHILDREN_TABLE,
    ENTITY_TYPE,
    GSI1_PK,
    GSI1_SK,
    PARTITION_KEY,
    SESSIONS_TABLE,
    SORT_KEY,
    USERS_TABLE,
    WORKSHEETS_TABLE,
    Child,
    Session,
    User,
    Worksheet,
)


class DynamoDBClient:
    """DynamoDB client wrapper."""

    def __init__(self):
        """Initialize DynamoDB client."""
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.getenv("AWS_REGION", "us-west-2"),
            endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL"),  # For local development
        )
        self.users_table = self.dynamodb.Table(USERS_TABLE)
        self.children_table = self.dynamodb.Table(CHILDREN_TABLE)
        self.sessions_table = self.dynamodb.Table(SESSIONS_TABLE)
        self.worksheets_table = self.dynamodb.Table(WORKSHEETS_TABLE)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        response = self.users_table.get_item(
            Key={
                PARTITION_KEY: User.get_pk(email),
                SORT_KEY: "METADATA",
            }
        )
        item = response.get("Item")
        if not item:
            return None

        return User(
            email=item["email"],
            name=item["name"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )

    def create_user(self, user: User) -> None:
        """Create a new user."""
        self.users_table.put_item(Item=user.to_item())

    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Get user by session ID."""
        response = self.sessions_table.get_item(
            Key={
                PARTITION_KEY: Session.get_pk(session_id),
                SORT_KEY: "METADATA",
            }
        )
        item = response.get("Item")
        if not item:
            return None

        return self.get_user_by_email(item["user_email"])

    def create_session(self, session: Session) -> None:
        """Create a new session."""
        self.sessions_table.put_item(Item=session.to_item())

    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        self.sessions_table.delete_item(
            Key={
                PARTITION_KEY: Session.get_pk(session_id),
                SORT_KEY: "METADATA",
            }
        )

    def get_children(self, parent_email: str) -> List[Child]:
        """Get all children for a parent."""
        response = self.children_table.query(
            KeyConditionExpression=Key(PARTITION_KEY).eq(User.get_pk(parent_email))
            & Key(SORT_KEY).begins_with("CHILD#"),
        )
        items = response.get("Items", [])
        return [
            Child(
                id=item["id"],
                parent_email=item["parent_email"],
                name=item["name"],
                birthday=datetime.fromisoformat(item["birthday"]),
                grade=item["grade"],
                preferred_color=item.get("preferred_color"),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
            )
            for item in items
        ]

    def get_child(self, child_id: str) -> Optional[Child]:
        """Get child by ID."""
        response = self.children_table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key(GSI1_PK).eq(Child.get_sk(child_id))
            & Key(GSI1_SK).eq("METADATA"),
        )
        items = response.get("Items", [])
        if not items:
            return None

        item = items[0]
        return Child(
            id=item["id"],
            parent_email=item["parent_email"],
            name=item["name"],
            birthday=datetime.fromisoformat(item["birthday"]),
            grade=item["grade"],
            preferred_color=item.get("preferred_color"),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )

    def create_child(self, child: Child) -> None:
        """Create a new child."""
        self.children_table.put_item(Item=child.to_item())

    def update_child(self, child: Child) -> None:
        """Update a child."""
        self.children_table.put_item(Item=child.to_item())

    def delete_child(self, child_id: str, parent_email: str) -> None:
        """Delete a child."""
        self.children_table.delete_item(
            Key={
                PARTITION_KEY: User.get_pk(parent_email),
                SORT_KEY: Child.get_sk(child_id),
            }
        )

    def create_worksheet(self, worksheet: Worksheet) -> None:
        """Create a new worksheet."""
        self.worksheets_table.put_item(Item=worksheet.to_item())

    def get_worksheets(self, child_id: str) -> List[Worksheet]:
        """Get all worksheets for a child."""
        response = self.worksheets_table.query(
            KeyConditionExpression=Key(PARTITION_KEY).eq(Worksheet.get_pk(child_id))
            & Key(SORT_KEY).begins_with("WORKSHEET#"),
        )
        items = response.get("Items", [])
        return [
            Worksheet(
                id=item["id"],
                child_id=item["child_id"],
                parent_email=item["parent_email"],
                problems=item["problems"],
                created_at=datetime.fromisoformat(item["created_at"]),
            )
            for item in items
        ]
