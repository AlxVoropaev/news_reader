# News Reader

A special CLI Telegram client built with Telethon library for reading news and messages, featuring MTProto server configuration and Docker Compose deployment.

## Features

- 🚀 **CLI Interface**: Simple command-line interface for Telegram connection
- 🔐 **MTProto Support**: Direct MTProto server IP address and public key configuration
- 📱 **Telegram Connection**: Secure connection and authorization to Telegram
- 🐳 **Docker Support**: Containerized deployment with Docker Compose
- 📡 **Real-time Monitoring**: Optional monitoring service for incoming messages
- 📺 **Channel Management**: List and select specific channels for monitoring
- 🗄️ **Local Database**: pysonDB-based local JSON database for storing configuration
- 🎨 **Colored Output**: Beautiful colored terminal output

## Prerequisites

- **For Docker setup**: Docker and Docker Compose
- **For Virtual Environment setup**: Python 3.7+ and virtualenvwrapper
- Telegram API credentials (API ID and API Hash)
- Phone number registered with Telegram

## Quick Start

### 1. Get Telegram API Credentials

1. Go to [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your phone number
3. Create a new application
4. Note down your `API ID` and `API Hash`

### 2. Setup

The setup script now supports both Docker and Python virtual environment:

```bash
# Clone or download the project
cd news_reader

# Run the interactive setup script
./setup.sh

# Choose your preferred setup method:
# 1) Docker (recommended for production)
# 2) Python Virtual Environment (recommended for development)

# Edit the .env file with your credentials
nano .env
```

#### Option 1: Docker Setup
- Automatically builds Docker containers
- Isolated environment
- Easy deployment and scaling
- No local Python dependencies needed

#### Option 2: Virtual Environment Setup
- Uses `mkvirtualenv` to create isolated Python environment
- Direct Python execution (faster for development)
- Better for debugging and development
- Requires Python 3.7+ and virtualenvwrapper

**Installing virtualenvwrapper (if not already installed):**
```bash
# Install virtualenvwrapper
pip3 install virtualenvwrapper

# Add to your ~/.bashrc or ~/.zshrc
echo 'export WORKON_HOME=$HOME/.virtualenvs' >> ~/.bashrc
echo 'export PROJECT_HOME=$HOME/Devel' >> ~/.bashrc
echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bashrc

# Reload your shell configuration
source ~/.bashrc
```

### 3. Configure Environment

Edit the `.env` file with your credentials:

```env
# Telegram API credentials
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890

# MTProto server configuration (default values work for most cases)
MTPROTO_SERVER_IP=149.154.167.50
MTPROTO_SERVER_PORT=443
MTPROTO_PUBLIC_KEY=-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEAwVACPi9w23mF/S2lqbz7xWWdvuYcuqnBDqpAJGI2PSPSfIFsmplW
RTD/33CWgQe6OaVldqOdGpWpn3EQ3ym3hAXfRZNEr/+BqQXn+F8jmTfFrQGx8+9J
8S4tEqYlNYIlnHtqMNoFk1NHpJ/hpQXn+F8jmTfFrQGx8+9J8S4tEqYlNYIlnHtq
MNoFk1NHpJ/hpQXn+F8jmTfFrQGx8+9J8S4tEqYlNYIlnHtqMNoFk1NHpJ/hpQXn
+F8jmTfFrQGx8+9J8S4tEqYlNYIlnHtqMNoFk1NHpJ/hpQXn+F8jmTfFrQGx8+9J
8S4tEqYlNYIlnHtqMNoFk1NHpJ/hpQXn+F8jmTfFrQGx8+9J8S4tEqYlNYIlnHtq
QIDAQAB
-----END RSA PUBLIC KEY-----

# Session settings
SESSION_NAME=news_reader_session
```

### 3. First Time Authorization

#### For Docker Setup:
```bash
# Connect and authorize for the first time
docker-compose run --rm news-reader connect
```

#### For Virtual Environment Setup:
```bash
# Activate the virtual environment
workon news-reader

# Connect and authorize for the first time
python news_reader.py connect
```

Follow the prompts to enter your phone number, verification code, and 2FA password if enabled.

## Usage

### Basic Commands

#### Docker Commands:
```bash
# Connect and authorize
docker-compose run --rm news-reader connect

# List all your channels
docker-compose run --rm news-reader channels

# Setup channel monitoring (select which channels to monitor)
docker-compose run --rm news-reader setup-monitoring
```

#### Virtual Environment Commands:

**Option A: Using the helper script (recommended):**
```bash
# Connect and authorize
./run_venv.sh connect

# List all your channels
./run_venv.sh channels

# Setup channel monitoring (select which channels to monitor)
./run_venv.sh setup-monitoring
```

**Option B: Manual activation:**
```bash
# First, activate the environment
workon news-reader

# Connect and authorize
python news_reader.py connect

# List all your channels
python news_reader.py channels

# Setup channel monitoring (select which channels to monitor)
python news_reader.py setup-monitoring
```

### Real-time Monitoring

**Note:** Before starting monitoring, make sure to run `setup-monitoring` to select which channels you want to monitor. The monitor will only show messages from your selected channels.

**Database Storage:** Channel configurations are stored in the `data/` directory using pysonDB. This directory is automatically created and the database files are stored locally for easy backup.

#### Docker Monitoring:
```bash
# Start monitoring service
docker-compose up news-reader-monitor

# Or run in background
docker-compose up -d news-reader-monitor

# View logs
docker-compose logs -f news-reader-monitor
```

#### Virtual Environment Monitoring:
```bash
# Using helper script
./run_venv.sh monitor

# Or manually
workon news-reader
python monitor.py
```

### Interactive Mode

```bash
# Run the container interactively
docker-compose run --rm news-reader bash

# Then use the CLI directly
python news_reader.py connect
```

## Project Structure

```
news_reader/
├── news_reader.py        # Main CLI client
├── monitor.py             # Real-time monitoring service
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
├── setup.sh              # Interactive setup script (Docker + virtualenv)
├── run_venv.sh           # Helper script for virtual environment
├── env.example           # Environment variables template
├── .dockerignore         # Docker ignore rules
├── README.md             # This file
└── sessions/             # Session files directory
```

## Configuration

### MTProto Server Settings

The client supports custom MTProto server configuration:

- `MTPROTO_SERVER_IP`: IP address of the MTProto server
- `MTPROTO_SERVER_PORT`: Port of the MTProto server
- `MTPROTO_PUBLIC_KEY`: Public key for the MTProto server

Default values are configured for Telegram's official servers, but you can modify them for custom implementations.

### Session Management

Sessions are stored in the `sessions/` directory and mounted as a Docker volume. This ensures your authorization persists between container restarts.

## Docker Commands

```bash
# Build the image
docker-compose build

# Connect and authorize
docker-compose run --rm news-reader connect

# Start monitoring service
docker-compose up news-reader-monitor

# Stop all services
docker-compose down

# View logs
docker-compose logs news-reader
docker-compose logs news-reader-monitor

# Clean up
docker-compose down -v
docker system prune
```

## Troubleshooting

### Common Issues

1. **Authorization Required**
   ```bash
   # Re-run the connect command
   docker-compose run --rm news-reader connect
   ```

2. **Session File Issues**
   ```bash
   # Clear sessions and re-authorize
   rm -rf sessions/*
   docker-compose run --rm news-reader connect
   ```

3. **API Credentials Invalid**
   - Double-check your API ID and API Hash in the `.env` file
   - Ensure there are no extra spaces or quotes

4. **Phone Number Format**
   - Use international format: `+1234567890`
   - Include the country code

### Debug Mode

Enable debug logging by modifying the `docker-compose.yml`:

```yaml
environment:
  - PYTHONPATH=/app
  - PYTHONUNBUFFERED=1
  - TELETHON_LOG_LEVEL=DEBUG
```

## Security Notes

- Never commit your `.env` file to version control
- Session files contain sensitive authentication data
- Use strong 2FA passwords
- Consider using a dedicated API application for this client

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Docker Compose
5. Submit a pull request

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Docker Compose logs
3. Ensure all prerequisites are met
4. Verify your Telegram API credentials
