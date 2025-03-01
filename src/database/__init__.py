"""Database package initialization."""

import os
from typing import Optional

import boto3
from botocore.config import Config

from .create_tables import create_tables as create_dynamodb_tables
from .repository import DynamoDBRepository

_repository: Optional[DynamoDBRepository] = None

# Get DynamoDB configuration from environment variables
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Configure boto3 client
config = Config(region_name=AWS_REGION, retries=dict(max_attempts=10))

# Initialize DynamoDB client with appropriate configuration
dynamodb_args = {
    "region_name": AWS_REGION,
    "config": config,
}

# Only add endpoint_url for local development
if DYNAMODB_ENDPOINT:
    dynamodb_args["endpoint_url"] = DYNAMODB_ENDPOINT

# Add credentials if provided
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    dynamodb_args["aws_access_key_id"] = AWS_ACCESS_KEY_ID
    dynamodb_args["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", **dynamodb_args)


def get_repository() -> DynamoDBRepository:
    """Get or create the DynamoDB repository instance."""
    global _repository
    if _repository is None:
        _repository = DynamoDBRepository()
    return _repository


def init_db(app):
    """Initialize the database with the Flask application."""
    app.config["DYNAMODB_CLIENT"] = dynamodb


def create_tables():
    """Create DynamoDB tables if they don't exist."""
    create_dynamodb_tables(dynamodb)
