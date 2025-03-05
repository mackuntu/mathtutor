#!/bin/bash

# Run UI tests for MathTutor application

# Create directories for test reports and screenshots
mkdir -p tests/ui/test-reports/screenshots

# Check if Flask server is running
if ! curl -s http://localhost:5000 > /dev/null; then
    echo "Starting Flask server..."
    # Start Flask server in the background
    cd ../.. && flask run &
    FLASK_PID=$!
    
    # Wait for server to start
    echo "Waiting for Flask server to start..."
    sleep 5
    
    # Set flag to kill server at the end
    KILL_SERVER=true
    # Go back to the UI tests directory
    cd tests/ui
else
    echo "Flask server is already running."
    KILL_SERVER=false
fi

# Install UI test dependencies if needed
if ! pip list | grep -q "selenium"; then
    echo "Installing UI test dependencies..."
    pip install -r requirements.txt
fi

# Run the UI tests
echo "Running UI tests..."
python -m pytest . "$@"

# Store the test result
TEST_RESULT=$?

# Kill Flask server if we started it
if [ "$KILL_SERVER" = true ]; then
    echo "Stopping Flask server..."
    cd ../..
    kill $FLASK_PID
fi

# Print test report location
echo "Test report available at: file://$(pwd)/tests/ui/test-reports/ui-report.html"

# Exit with the test result
exit $TEST_RESULT 