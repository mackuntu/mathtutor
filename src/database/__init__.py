"""Database package initialization."""

from typing import Optional

from .repository import DynamoDBRepository

_repository: Optional[DynamoDBRepository] = None


def get_repository() -> DynamoDBRepository:
    """Get or create the DynamoDB repository instance."""
    global _repository
    if _repository is None:
        _repository = DynamoDBRepository()
    return _repository
