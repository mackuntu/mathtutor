"""Configuration settings for DynamoDB."""

# Table names
USERS_TABLE = "Users"
CHILDREN_TABLE = "Children"
SESSIONS_TABLE = "Sessions"
WORKSHEETS_TABLE = "Worksheets"

# Index names
PARENT_EMAIL_INDEX = "ParentEmailIndex"
USER_EMAIL_INDEX = "UserEmailIndex"
CHILD_ID_INDEX = "ChildIdIndex"

# TTL attribute name for sessions
SESSION_TTL_ATTRIBUTE = "expires_at"
