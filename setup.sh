#!/bin/bash

# AI Canvas Backend Setup Script

echo "🚀 Setting up AI Canvas Backend..."

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment
echo "🔨 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  uvicorn main:app --reload"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Docs will be available at: http://localhost:8000/docs"
