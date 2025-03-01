#!/usr/bin/env python
"""Script to create DynamoDB tables in AWS."""

import os
import sys
import time

import boto3
from botocore.exceptions import ClientError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the table definitions
from src.database import create_tables


def main():
    """Create DynamoDB tables in AWS."""
    print("Creating DynamoDB tables...")

    # Create tables using the application's create_tables function
    create_tables()

    print("DynamoDB tables created successfully.")


if __name__ == "__main__":
    main()
