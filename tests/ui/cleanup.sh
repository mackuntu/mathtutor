#!/bin/bash

# Script to clean up unnecessary files and standardize the UI test directory structure

echo "Cleaning up UI test directory..."

# Create the standardized directories
mkdir -p tests/ui/test-reports/screenshots

# Move important screenshots from old locations to the standardized location
if [ -d "tests/ui/screenshot" ]; then
    echo "Moving important screenshots from old location..."
    find tests/ui/screenshot -name "*.png" -type f -exec cp {} tests/ui/test-reports/screenshots/ \;
    echo "Removing old screenshot directory..."
    rm -rf tests/ui/screenshot
fi

# Remove old test scripts that are now replaced by run_all_tests.sh
if [ -f "tests/ui/run_ui_tests.sh" ]; then
    echo "Removing old run_ui_tests.sh script..."
    rm tests/ui/run_ui_tests.sh
fi

if [ -f "tests/ui/run_worksheet_tests.sh" ]; then
    echo "Removing old run_worksheet_tests.sh script..."
    rm tests/ui/run_worksheet_tests.sh
fi

# Remove __pycache__ directories
echo "Removing __pycache__ directories..."
find tests/ui -name "__pycache__" -type d -exec rm -rf {} +

# Remove .pytest_cache directory
if [ -d "tests/ui/.pytest_cache" ]; then
    echo "Removing .pytest_cache directory..."
    rm -rf tests/ui/.pytest_cache
fi

# Remove any error screenshots in the root directory
echo "Removing error screenshots from root directory..."
rm -f error_*.png
rm -f *_screenshot.png

echo "Cleanup complete!" 