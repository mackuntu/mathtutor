"""Repository class for DynamoDB operations."""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import boto3

from .config import (
    CHILD_ID_INDEX,
    CHILDREN_TABLE,
    PARENT_EMAIL_INDEX,
    PAYMENTS_TABLE,
    SESSION_TTL_ATTRIBUTE,
    SESSIONS_TABLE,
    SUBSCRIPTIONS_TABLE,
    USER_EMAIL_INDEX,
    USER_EMAIL_PAYMENT_INDEX,
    USER_EMAIL_SUBSCRIPTION_INDEX,
    USERS_TABLE,
    WORKSHEETS_TABLE,
)
from .models import Child, Payment, Session, Subscription, User
from .models import Worksheet as WorksheetModel


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

    def scan_users(self) -> List[User]:
        """Scan all users."""
        response = self.dynamodb.scan(TableName=USERS_TABLE)
        return [User.from_item(item) for item in response.get("Items", [])]

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
    def get_worksheet(self, worksheet_id: str) -> Optional[WorksheetModel]:
        """Get worksheet by ID."""
        response = self.dynamodb.get_item(
            TableName=WORKSHEETS_TABLE, Key={"id": {"S": worksheet_id}}
        )
        item = response.get("Item")
        if not item:
            return None

        return WorksheetModel.from_dict(
            {
                "id": item["id"]["S"],
                "child_id": item["child_id"]["S"],
                "problems": item["problems"]["S"],
                "created_at": datetime.fromtimestamp(int(item["created_at"]["N"])),
                "updated_at": datetime.fromtimestamp(int(item["updated_at"]["N"])),
                "serial_number": item.get("serial_number", {}).get("S"),
                "incorrect_problems": item.get("incorrect_problems", {}).get("S"),
                "answers": item.get("answers", {}).get("S"),
                "completed": item.get("completed", {}).get("BOOL", False),
            }
        )

    def get_child_worksheets(self, child_id: str) -> List[WorksheetModel]:
        """Get all worksheets for a child."""
        response = self.dynamodb.query(
            TableName=WORKSHEETS_TABLE,
            IndexName=CHILD_ID_INDEX,
            KeyConditionExpression="child_id = :child_id",
            ExpressionAttributeValues={":child_id": {"S": child_id}},
        )
        return [
            WorksheetModel.from_dict(
                {
                    "id": item["id"]["S"],
                    "child_id": item["child_id"]["S"],
                    "problems": item["problems"]["S"],
                    "created_at": datetime.fromtimestamp(int(item["created_at"]["N"])),
                    "updated_at": datetime.fromtimestamp(int(item["updated_at"]["N"])),
                    "serial_number": item.get("serial_number", {}).get("S"),
                    "incorrect_problems": item.get("incorrect_problems", {}).get("S"),
                    "answers": item.get("answers", {}).get("S"),
                    "completed": item.get("completed", {}).get("BOOL", False),
                }
            )
            for item in response.get("Items", [])
        ]

    def create_worksheet(self, worksheet: WorksheetModel) -> None:
        """Create a new worksheet."""
        # Build the item dictionary
        item = {
            "id": {"S": worksheet.id},
            "child_id": {"S": worksheet.child_id},
            "completed": {"BOOL": worksheet.completed},
        }

        # Handle problems which could be a list or a string
        if isinstance(worksheet.problems, list):
            item["problems"] = {"S": json.dumps(worksheet.problems)}
        else:
            item["problems"] = {"S": worksheet.problems}

        # Handle created_at and updated_at which could be datetime or int
        if isinstance(worksheet.created_at, datetime):
            item["created_at"] = {"N": str(int(worksheet.created_at.timestamp()))}
        else:
            item["created_at"] = {"N": str(worksheet.created_at)}

        if isinstance(worksheet.updated_at, datetime):
            item["updated_at"] = {"N": str(int(worksheet.updated_at.timestamp()))}
        else:
            item["updated_at"] = {"N": str(worksheet.updated_at)}

        # Add serial_number if present and the attribute exists
        if hasattr(worksheet, "serial_number") and worksheet.serial_number:
            item["serial_number"] = {"S": worksheet.serial_number}

        # Always include incorrect_problems, even if it's an empty list
        if worksheet.incorrect_problems is not None:
            item["incorrect_problems"] = {"S": json.dumps(worksheet.incorrect_problems)}

        # Always include answers, even if it's an empty list
        if worksheet.answers is not None:
            item["answers"] = {"S": json.dumps(worksheet.answers)}

        self.dynamodb.put_item(
            TableName=WORKSHEETS_TABLE,
            Item=item,
        )

    def update_worksheet(self, worksheet: WorksheetModel) -> None:
        """Update an existing worksheet."""
        worksheet.updated_at = datetime.utcnow()

        # Build the item dictionary
        item = {
            "id": {"S": worksheet.id},
            "child_id": {"S": worksheet.child_id},
            "completed": {"BOOL": worksheet.completed},
        }

        # Handle problems which could be a list or a string
        if isinstance(worksheet.problems, list):
            item["problems"] = {"S": json.dumps(worksheet.problems)}
        else:
            item["problems"] = {"S": worksheet.problems}

        # Handle created_at and updated_at which could be datetime or int
        if isinstance(worksheet.created_at, datetime):
            item["created_at"] = {"N": str(int(worksheet.created_at.timestamp()))}
        else:
            item["created_at"] = {"N": str(worksheet.created_at)}

        if isinstance(worksheet.updated_at, datetime):
            item["updated_at"] = {"N": str(int(worksheet.updated_at.timestamp()))}
        else:
            item["updated_at"] = {"N": str(worksheet.updated_at)}

        # Add serial_number if present
        if hasattr(worksheet, "serial_number") and worksheet.serial_number:
            item["serial_number"] = {"S": worksheet.serial_number}

        # Always include incorrect_problems, even if it's an empty list
        if worksheet.incorrect_problems is not None:
            item["incorrect_problems"] = {"S": json.dumps(worksheet.incorrect_problems)}

        # Always include answers, even if it's an empty list
        if worksheet.answers is not None:
            item["answers"] = {"S": json.dumps(worksheet.answers)}

        self.dynamodb.put_item(
            TableName=WORKSHEETS_TABLE,
            Item=item,
        )

    def delete_worksheet(self, worksheet_id: str) -> None:
        """Delete a worksheet."""
        self.dynamodb.delete_item(
            TableName=WORKSHEETS_TABLE, Key={"id": {"S": worksheet_id}}
        )

    # Subscription operations
    def get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID."""
        response = self.dynamodb.get_item(
            TableName=SUBSCRIPTIONS_TABLE, Key={"id": {"S": subscription_id}}
        )
        return Subscription.from_item(response.get("Item"))

    def get_user_subscription(self, user_email: str) -> Optional[Subscription]:
        """Get subscription for a user."""
        response = self.dynamodb.query(
            TableName=SUBSCRIPTIONS_TABLE,
            IndexName=USER_EMAIL_SUBSCRIPTION_INDEX,
            KeyConditionExpression="user_email = :email",
            ExpressionAttributeValues={":email": {"S": user_email}},
            ScanIndexForward=False,  # Sort by most recent
            Limit=1,
        )

        items = response.get("Items", [])
        if not items:
            return None

        return Subscription.from_item(items[0])

    def create_subscription(self, subscription: Subscription) -> None:
        """Create a new subscription."""
        self.dynamodb.put_item(
            TableName=SUBSCRIPTIONS_TABLE, Item=subscription.to_item()
        )

    def update_subscription(self, subscription: Subscription) -> None:
        """Update an existing subscription."""
        self.dynamodb.put_item(
            TableName=SUBSCRIPTIONS_TABLE, Item=subscription.to_item()
        )

    def delete_subscription(self, subscription_id: str) -> None:
        """Delete a subscription."""
        self.dynamodb.delete_item(
            TableName=SUBSCRIPTIONS_TABLE, Key={"id": {"S": subscription_id}}
        )

    def scan_subscriptions(self) -> List[Subscription]:
        """Scan all subscriptions."""
        response = self.dynamodb.scan(TableName=SUBSCRIPTIONS_TABLE)
        return [Subscription.from_item(item) for item in response.get("Items", [])]

    # Payment operations
    def get_payment_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID."""
        response = self.dynamodb.get_item(
            TableName=PAYMENTS_TABLE, Key={"id": {"S": payment_id}}
        )
        return Payment.from_item(response.get("Item"))

    def get_user_payments(self, user_email: str) -> List[Payment]:
        """Get payments for a user."""
        response = self.dynamodb.query(
            TableName=PAYMENTS_TABLE,
            IndexName=USER_EMAIL_PAYMENT_INDEX,
            KeyConditionExpression="user_email = :email",
            ExpressionAttributeValues={":email": {"S": user_email}},
            ScanIndexForward=False,  # Sort by most recent
        )

        return [Payment.from_item(item) for item in response.get("Items", [])]

    def create_payment(self, payment: Payment) -> None:
        """Create a new payment."""
        self.dynamodb.put_item(TableName=PAYMENTS_TABLE, Item=payment.to_item())

    def update_payment(self, payment: Payment) -> None:
        """Update an existing payment."""
        self.dynamodb.put_item(TableName=PAYMENTS_TABLE, Item=payment.to_item())

    def delete_payment(self, payment_id: str) -> None:
        """Delete a payment."""
        self.dynamodb.delete_item(
            TableName=PAYMENTS_TABLE, Key={"id": {"S": payment_id}}
        )


_repository_instance = None


def get_repository() -> DynamoDBRepository:
    """Get or create a DynamoDBRepository instance."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = DynamoDBRepository()
    return _repository_instance
