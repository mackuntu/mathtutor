"""Database configuration and initialization."""

import os

import boto3
from botocore.config import Config

# Get DynamoDB configuration from environment variables
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "dummy")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")

# Configure boto3 client
config = Config(region_name=AWS_REGION, retries=dict(max_attempts=10))

# Initialize DynamoDB client
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=config,
)


def init_db(app):
    """Initialize the database with the Flask application."""
    app.config["DYNAMODB_CLIENT"] = dynamodb


def get_table(table_name: str):
    """Get a DynamoDB table.

    Args:
        table_name: Name of the table

    Returns:
        Table: DynamoDB table resource
    """
    return dynamodb.Table(table_name)


def create_tables():
    """Create DynamoDB tables if they don't exist."""
    # Define table schemas here
    tables = {
        "Users": {
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "EmailIndex",
                    "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        },
        "Children": {
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "parent_id", "AttributeType": "S"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "ParentIndex",
                    "KeySchema": [{"AttributeName": "parent_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        },
        "Worksheets": {
            "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "child_id", "AttributeType": "S"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "ChildIndex",
                    "KeySchema": [{"AttributeName": "child_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        },
    }

    existing_tables = [table.name for table in dynamodb.tables.all()]

    for table_name, schema in tables.items():
        if table_name not in existing_tables:
            try:
                dynamodb.create_table(TableName=table_name, **schema)
                print(f"Created table {table_name}")
            except Exception as e:
                print(f"Error creating table {table_name}: {str(e)}")
