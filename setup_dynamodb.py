#!/usr/bin/env python
"""Script to set up DynamoDB tables locally."""

import os

import boto3
from botocore.exceptions import ClientError

# Set environment variables for local development
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_REGION"] = "us-east-1"

# Connect to local DynamoDB
dynamodb = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    aws_access_key_id="testing",
    aws_secret_access_key="testing",
    region_name="us-east-1",
)

# Table names from config
USERS_TABLE = "Users"
CHILDREN_TABLE = "Children"
SESSIONS_TABLE = "Sessions"
WORKSHEETS_TABLE = "Worksheets"
SUBSCRIPTIONS_TABLE = "mathtutor-subscriptions"
PAYMENTS_TABLE = "mathtutor-payments"

# Index names
PARENT_EMAIL_INDEX = "ParentEmailIndex"
USER_EMAIL_INDEX = "UserEmailIndex"
CHILD_ID_INDEX = "ChildIdIndex"
USER_EMAIL_SUBSCRIPTION_INDEX = "user-email-index"
USER_EMAIL_PAYMENT_INDEX = "user-email-index"


def create_table_if_not_exists(
    table_name,
    key_schema,
    attribute_definitions,
    global_secondary_indexes=None,
    provisioned_throughput=None,
):
    """Create a table if it doesn't exist."""
    try:
        print(f"Creating {table_name} table...")
        params = {
            "TableName": table_name,
            "KeySchema": key_schema,
            "AttributeDefinitions": attribute_definitions,
            "ProvisionedThroughput": provisioned_throughput
            or {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }

        if global_secondary_indexes:
            params["GlobalSecondaryIndexes"] = global_secondary_indexes

        dynamodb.create_table(**params)
        print(f"Table {table_name} created successfully!")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table {table_name} already exists.")
        else:
            print(f"Error creating table {table_name}: {e}")
            raise


# Create Users table
create_table_if_not_exists(
    table_name=USERS_TABLE,
    key_schema=[
        {"AttributeName": "email", "KeyType": "HASH"},  # Partition key
    ],
    attribute_definitions=[
        {"AttributeName": "email", "AttributeType": "S"},
    ],
)

# Create Children table
create_table_if_not_exists(
    table_name=CHILDREN_TABLE,
    key_schema=[
        {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
    ],
    attribute_definitions=[
        {"AttributeName": "id", "AttributeType": "S"},
        {"AttributeName": "parent_email", "AttributeType": "S"},
    ],
    global_secondary_indexes=[
        {
            "IndexName": PARENT_EMAIL_INDEX,
            "KeySchema": [
                {"AttributeName": "parent_email", "KeyType": "HASH"},
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }
    ],
)

# Create Sessions table
create_table_if_not_exists(
    table_name=SESSIONS_TABLE,
    key_schema=[
        {"AttributeName": "token", "KeyType": "HASH"},  # Partition key
    ],
    attribute_definitions=[
        {"AttributeName": "token", "AttributeType": "S"},
        {"AttributeName": "user_email", "AttributeType": "S"},
    ],
    global_secondary_indexes=[
        {
            "IndexName": USER_EMAIL_INDEX,
            "KeySchema": [
                {"AttributeName": "user_email", "KeyType": "HASH"},
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }
    ],
)

# Create Worksheets table
create_table_if_not_exists(
    table_name=WORKSHEETS_TABLE,
    key_schema=[
        {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
    ],
    attribute_definitions=[
        {"AttributeName": "id", "AttributeType": "S"},
        {"AttributeName": "child_id", "AttributeType": "S"},
    ],
    global_secondary_indexes=[
        {
            "IndexName": CHILD_ID_INDEX,
            "KeySchema": [
                {"AttributeName": "child_id", "KeyType": "HASH"},
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }
    ],
)

# Create Subscriptions table
create_table_if_not_exists(
    table_name=SUBSCRIPTIONS_TABLE,
    key_schema=[
        {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
    ],
    attribute_definitions=[
        {"AttributeName": "id", "AttributeType": "S"},
        {"AttributeName": "user_email", "AttributeType": "S"},
    ],
    global_secondary_indexes=[
        {
            "IndexName": USER_EMAIL_SUBSCRIPTION_INDEX,
            "KeySchema": [
                {"AttributeName": "user_email", "KeyType": "HASH"},
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }
    ],
)

# Create Payments table
create_table_if_not_exists(
    table_name=PAYMENTS_TABLE,
    key_schema=[
        {"AttributeName": "id", "KeyType": "HASH"},  # Partition key
    ],
    attribute_definitions=[
        {"AttributeName": "id", "AttributeType": "S"},
        {"AttributeName": "user_email", "AttributeType": "S"},
    ],
    global_secondary_indexes=[
        {
            "IndexName": USER_EMAIL_PAYMENT_INDEX,
            "KeySchema": [
                {"AttributeName": "user_email", "KeyType": "HASH"},
            ],
            "Projection": {"ProjectionType": "ALL"},
            "ProvisionedThroughput": {"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        }
    ],
)

print("All tables checked/created successfully!")
