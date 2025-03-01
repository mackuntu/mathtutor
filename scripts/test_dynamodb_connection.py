#!/usr/bin/env python
"""Script to test the DynamoDB connection."""

import os
import sys

import boto3
from botocore.exceptions import ClientError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_connection():
    """Test the DynamoDB connection."""
    print("Testing DynamoDB connection...")

    # Get DynamoDB configuration from environment variables
    dynamodb_endpoint = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
    aws_region = os.getenv("AWS_REGION", "us-west-2")
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "dummy")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "dummy")

    print(f"Using endpoint: {dynamodb_endpoint}")
    print(f"Using region: {aws_region}")

    try:
        # Initialize DynamoDB client
        dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=dynamodb_endpoint,
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

        # List tables
        tables = list(dynamodb.tables.all())
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table.name}")

        print("DynamoDB connection successful!")
        return True
    except ClientError as e:
        print(f"Error connecting to DynamoDB: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
