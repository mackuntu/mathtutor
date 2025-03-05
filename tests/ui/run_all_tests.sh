#!/bin/bash

# Unified UI test script for MathTutor application
# Supports running all tests or specific test types

# Default settings
PORT=8080
TEST_TYPE="all"
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    --test=*)
      TEST_TYPE="${1#*=}"
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --port=PORT       Specify the port for Flask server (default: 8080)"
      echo "  --test=TYPE       Specify test type: all, worksheet, preview (default: all)"
      echo "  --verbose         Enable verbose output"
      echo "  --help            Display this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Store the original directory
ORIGINAL_DIR=$(pwd)

# Create directories for test reports and screenshots
mkdir -p tests/ui/test-reports/screenshots

# Check if Flask server is running
if ! nc -z localhost $PORT; then
    echo "Starting Flask server on port $PORT..."
    cd ../.. && python -m flask run --debug --port $PORT &
    FLASK_PID=$!
    
    # Wait for server to start
    echo "Waiting for Flask server to start..."
    sleep 5
    
    # Set flag to kill server at the end
    KILL_FLASK=true
else
    echo "Flask server is already running on port $PORT."
    KILL_FLASK=false
fi

# Navigate to the UI tests directory
cd "$ORIGINAL_DIR/tests/ui" || exit 1

# Install UI test dependencies if not already installed
if ! python -c "import selenium" &> /dev/null; then
    echo "Installing UI test dependencies..."
    pip install -r requirements.txt
fi

# Set pytest verbosity
PYTEST_ARGS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="-v"
fi

# Run the appropriate tests based on the test type
echo "Running UI tests: $TEST_TYPE"
case $TEST_TYPE in
    "worksheet")
        python -m pytest test_worksheet_generation.py::TestWorksheetGeneration::test_generate_and_delete_worksheet test_worksheet_generation.py::TestWorksheetGeneration::test_bulk_delete_worksheets $PYTEST_ARGS
        ;;
    "preview")
        python -m pytest test_worksheet_generation.py::TestWorksheetGeneration::test_preview_worksheet $PYTEST_ARGS
        ;;
    "all"|*)
        python -m pytest . $PYTEST_ARGS
        ;;
esac

# Store the test result
TEST_RESULT=$?

# Return to the original directory
cd "$ORIGINAL_DIR" || exit 1

# Kill Flask server if we started it
if [ "$KILL_FLASK" = true ]; then
    echo "Stopping Flask server..."
    if [ -n "$FLASK_PID" ]; then
        kill $FLASK_PID
    fi
fi

# Print test report location
echo "Test report generated at file://$(pwd)/tests/ui/test-reports/ui-report.html"

# Exit with the test result
exit $TEST_RESULT 