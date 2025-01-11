from setuptools import find_packages, setup


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    with open(filename, "r") as req_file:
        return [
            line.strip()
            for line in req_file.readlines()
            if line.strip() and not line.startswith("#")
        ]


setup(
    name="mathtutor",
    version="0.0.1",
    description="A Python project for creating, rendering, and grading math worksheets.",
    author="Martin Qian",
    author_email="martin@dichotomy.ai",
    packages=find_packages(
        exclude=[
            "tests",
            "examples",
            "*.local",
            "*.temp",
        ]  # Exclude specific directories or patterns
    ),
    install_requires=parse_requirements(
        "requirements.txt"
    ),  # Read dependencies from requirements.txt
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
