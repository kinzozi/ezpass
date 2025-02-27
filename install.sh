#!/bin/bash

# Check if Python 3.6+ is installed
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )([0-9]+\.[0-9]+)')
if [[ -z "$python_version" ]]; then
    echo "Python 3 is not installed. Please install Python 3.6 or higher."
    exit 1
fi

major_version=$(echo $python_version | cut -d. -f1)
minor_version=$(echo $python_version | cut -d. -f2)

if [[ $major_version -lt 3 || ($major_version -eq 3 && $minor_version -lt 6) ]]; then
    echo "Python 3.6 or higher is required. Found Python $python_version"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3."
    exit 1
fi

# Install dependencies
echo "Installing required Python packages..."
pip3 install -e .

# Check if clipboard utilities are installed on Linux
if [[ "$(uname)" == "Linux" ]]; then
    if ! command -v xclip &> /dev/null && ! command -v xsel &> /dev/null; then
        echo "Warning: Neither xclip nor xsel is installed."
        echo "Clipboard functionality will not work without one of these utilities."
        echo "Install with: sudo apt-get install xclip   OR   sudo apt-get install xsel"
    fi
fi

echo "ezpass has been installed successfully!"
echo "Run 'ezpass -h' for usage instructions."