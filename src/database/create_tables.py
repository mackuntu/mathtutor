"""Create DynamoDB tables for the MathTutor application."""

import os

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_tables(dynamodb_resource=None):
    """Create DynamoDB tables if they don't exist.

    Args:
        dynamodb_resource: Optional boto3 DynamoDB resource. If not provided,
            a new client will be created with local development settings.
    """
    if dynamodb_resource is None:
        # Initialize DynamoDB client with local endpoint for development
        dynamodb_resource = boto3.resource(
            "dynamodb",
            endpoint_url=os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "testing"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "testing"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

    # Get DynamoDB client from resource
    dynamodb = dynamodb_resource.meta.client

    # Users table
    try:
        dynamodb.create_table(
            TableName="Users",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Users table created successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Users table already exists")
        else:
            raise

    # Children table
    try:
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
        print("Children table created successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Children table already exists")
        else:
            raise

    # Sessions table
    try:
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
        print("Sessions table created successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Sessions table already exists")
        else:
            raise

    # Worksheets table
    try:
        dynamodb.create_table(
            TableName="Worksheets",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "child_id", "AttributeType": "S"},
                {"AttributeName": "serial_number", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "ChildIdIndex",
                    "KeySchema": [{"AttributeName": "child_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "SerialNumberIndex",
                    "KeySchema": [
                        {"AttributeName": "serial_number", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Worksheets table created successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Worksheets table already exists")
        else:
            raise

    # Subscriptions table
    try:
        dynamodb.create_table(
            TableName="mathtutor-subscriptions",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "user_email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user-email-index",
                    "KeySchema": [{"AttributeName": "user_email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Subscriptions table created successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Subscriptions table already exists")
        else:
            raise

    # Payments table
    try:
        dynamodb.create_table(
            TableName="mathtutor-payments",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "user_email", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user-email-index",
                    "KeySchema": [{"AttributeName": "user_email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Payments table created successfully")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("Payments table already exists")
        else:
            raise


if __name__ == "__main__":
    create_tables()
