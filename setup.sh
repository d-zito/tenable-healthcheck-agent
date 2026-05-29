#!/bin/bash

echo "==============================================="
echo "Tenable Health Check Agent - Setup"
echo "==============================================="
echo

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python found: $(python3 --version)"

# Install dependencies
echo
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment."
    exit 1
fi

echo "✓ Virtual environment created"

echo
echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    exit 1
fi

echo "✓ Dependencies installed"

# Create config file
echo
if [ ! -f "config/config.json" ]; then
    echo "Creating configuration file..."
    cp config/config.example.json config/config.json
    echo "✓ Configuration file created at config/config.json"
    echo
    echo "IMPORTANT: Please edit config/config.json and add your Tenable credentials:"
    echo "  - access_key: Your Tenable API access key"
    echo "  - secret_key: Your Tenable API secret key"
    echo
else
    echo "✓ Configuration file already exists"
fi

# Create data directory
mkdir -p data/history
echo "✓ Data directory created"

# Make main script executable
chmod +x src/main.py

echo
echo "==============================================="
echo "Setup Complete!"
echo "==============================================="
echo
echo "Next steps:"
echo "1. Edit config/config.json with your Tenable credentials"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Run the health check: python3 src/main.py"
echo
echo "NOTE: You must activate the virtual environment each time:"
echo "  source venv/bin/activate"
echo
