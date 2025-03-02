#!/bin/bash

# Create the icons directory if it doesn't exist
mkdir -p src/static/images/icons

# Copy the icon files from the assets directory to the correct location
cp assets/mathtutor_icon_192.png src/static/images/icons/
cp assets/mathtutor_icon_512.png src/static/images/icons/
cp assets/favicon.ico src/static/images/icons/

echo "Icon files copied successfully!" 