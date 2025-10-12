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
    cp env.example .env
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

    # Check if virtualenvwrapper is installed
    if ! command -v mkvirtualenv &> /dev/null; then
        echo -e "${YELLOW}⚠️  virtualenvwrapper not found. Installing...${NC}"
        
        # Try to install virtualenvwrapper
        if command -v pip3 &> /dev/null; then
            pip3 install virtualenvwrapper
        elif command -v pip &> /dev/null; then
            pip install virtualenvwrapper
        else
            echo -e "${RED}❌ pip not found. Please install pip first.${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}📝 Please add these lines to your ~/.bashrc or ~/.zshrc:${NC}"
        echo "export WORKON_HOME=\$HOME/.virtualenvs"
        echo "export PROJECT_HOME=\$HOME/Devel"
        echo "source /usr/local/bin/virtualenvwrapper.sh"
        echo ""
        echo -e "${YELLOW}Then run: source ~/.bashrc (or ~/.zshrc)${NC}"
        echo -e "${YELLOW}After that, run this script again.${NC}"
        exit 1
    fi

    # Create virtual environment
    ENV_NAME="news-reader"
    echo -e "${YELLOW}🔨 Creating virtual environment '${ENV_NAME}'...${NC}"
    
    if mkvirtualenv -p python3 "$ENV_NAME"; then
        echo -e "${GREEN}✅ Virtual environment created successfully${NC}"
    else
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    fi

    # Activate virtual environment and install dependencies
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
    source "$WORKON_HOME/$ENV_NAME/bin/activate"
    pip install -r requirements.txt

    echo -e "${GREEN}✅ Virtual environment setup completed!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next steps (Virtual Environment):${NC}"
    echo "1. Edit .env file with your Telegram API credentials"
    echo "2. Activate the environment: workon $ENV_NAME"
    echo "3. Run: python news_reader.py connect"
    echo "4. Follow the authorization process"
    echo ""
    echo -e "${YELLOW}🔍 To start monitoring: python monitor.py${NC}"
    echo ""
    echo -e "${BLUE}💡 Remember to activate the environment before using:${NC}"
    echo -e "${YELLOW}   workon $ENV_NAME${NC}"
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
