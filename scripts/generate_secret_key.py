#!/usr/bin/env python
"""Generate a secure secret key for Flask."""

import os
import secrets
import sys


def generate_secret_key(length=32):
    """Generate a secure random string for use as a Flask secret key.

    Args:
        length: Length of the secret key in bytes

    Returns:
        str: Hexadecimal string representation of the secret key
    """
    return secrets.token_hex(length)


if __name__ == "__main__":
    # Get the length from command line arguments, default to 32
    length = 32
    if len(sys.argv) > 1:
        try:
            length = int(sys.argv[1])
        except ValueError:
            print(
                f"Error: Length must be an integer. Using default length of {length}."
            )

    # Generate and print the secret key
    secret_key = generate_secret_key(length)
    print(f"Generated Flask Secret Key ({length} bytes):")
    print(secret_key)
