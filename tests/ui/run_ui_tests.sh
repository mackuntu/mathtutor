#!/bin/bash

# Run UI tests for MathTutor application

# Create directories for test reports and screenshots
mkdir -p test-reports/screenshots

# Check if Flask server is running
if ! nc -z localhost 8080; then
    echo "Starting Flask server..."
    cd ../.. && python -m flask run --debug --port 8080 &
    FLASK_PID=$!
    
    # Wait for server to start
    echo "Waiting for Flask server to start..."
    sleep 5
    
    # Set flag to kill server at the end
    KILL_FLASK=true
else
    echo "Flask server is already running."
    KILL_FLASK=false
fi

# Install UI test dependencies if not already installed
if ! python -c "import selenium" &> /dev/null; then
    echo "Installing UI test dependencies..."
    pip install -r requirements.txt
fi

# Run the UI tests
echo "Running UI tests..."
python -m pytest . "$@"

# Store the test result
TEST_RESULT=$?

# Kill Flask server if we started it
if [ "$KILL_FLASK" = true ]; then
    echo "Stopping Flask server..."
    kill $FLASK_PID
fi

# Print test report location
echo "Test report generated at file://$(pwd)/test-reports/ui-report.html"

# Exit with the test result
exit $TEST_RESULT 