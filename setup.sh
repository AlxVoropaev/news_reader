#!/bin/bash

# Telegram CLI Client Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up News Reader...${NC}"

# Create necessary directories
mkdir -p sessions
mkdir -p logs

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your Telegram API credentials!${NC}"
    echo -e "   You can get them from https://my.telegram.org/apps"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Function to setup with Docker
setup_docker() {
    echo -e "${BLUE}🐳 Setting up with Docker...${NC}"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Docker and Docker Compose are available${NC}"

    # Build the Docker image
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    docker-compose build

    echo -e "${GREEN}✅ Docker setup completed!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps (Docker):${NC}"
    echo "1. Edit .env file with your Telegram API credentials"
    echo "2. Run: docker-compose run --rm news-reader connect"
    echo "3. Follow the authorization process"
    echo ""
    echo -e "${YELLOW}🔍 To start monitoring: docker-compose up news-reader-monitor${NC}"
}

# Function to setup with virtualenv
setup_virtualenv() {
    echo -e "${BLUE}🐍 Setting up with Python virtual environment...${NC}"
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed. Please install Python 3 first.${NC}"
        exit 1
    fi

    # Create virtual environment using built-in venv module
    ENV_DIR=".venv"
    echo -e "${YELLOW}🔨 Creating virtual environment '${ENV_DIR}'...${NC}"
    
    if python3 -m venv "$ENV_DIR"; then
        echo -e "${GREEN}✅ Virtual environment created successfully${NC}"
    else
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi

    # Activate virtual environment and install dependencies
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    source "$ENV_DIR/bin/activate"
    pip install -r requirements.txt

    echo -e "${GREEN}✅ Virtual environment setup completed!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps (Virtual Environment):${NC}"
    echo "1. Edit .env file with your Telegram API credentials"
    echo "2. Use the helper script: ./run_venv.sh connect"
    echo "3. Follow the authorization process"
    echo ""
    echo -e "${YELLOW}🔍 To start monitoring: ./run_venv.sh monitor${NC}"
    echo ""
    echo -e "${BLUE}💡 Or manually activate the environment:${NC}"
    echo -e "${YELLOW}   source $ENV_DIR/bin/activate${NC}"
}

# Main menu
echo ""
echo -e "${BLUE}Please choose your setup method:${NC}"
echo "1) Docker (recommended for production)"
echo "2) Python Virtual Environment (recommended for development)"
echo ""
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        setup_docker
        ;;
    2)
        setup_virtualenv
        ;;
    *)
        echo -e "${RED}❌ Invalid choice. Please run the script again and choose 1 or 2.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
