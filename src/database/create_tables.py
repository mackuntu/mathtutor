"""Create DynamoDB tables for the MathTutor application."""

import os

import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_tables():
    """Create DynamoDB tables if they don't exist."""
    # Initialize DynamoDB client with local endpoint
    dynamodb = boto3.client(
        "dynamodb",
        endpoint_url="http://localhost:8000",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        region_name="us-east-1",
    )

    # Users table
    try:
        dynamodb.create_table(
            TableName="Users",
            KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Users table created successfully")
    except dynamodb.exceptions.ResourceInUseException:
        print("Users table already exists")

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
    except dynamodb.exceptions.ResourceInUseException:
        print("Children table already exists")

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
    except dynamodb.exceptions.ResourceInUseException:
        print("Sessions table already exists")

    # Worksheets table
    try:
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
        print("Worksheets table created successfully")
    except dynamodb.exceptions.ResourceInUseException:
        print("Worksheets table already exists")


if __name__ == "__main__":
    create_tables()
