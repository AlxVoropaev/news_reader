# News Reader

A specialized Telegram client that reads your newsfeed and uses an LLM to provide a daily summary.

![Interface](assets/interface.png)

## ✨ Key Features

- 🎨 **Modern Terminal UI**: Beautiful interactive interface powered by Textual library
- 📡 **Real-time Monitoring**: Live monitoring of your selected Telegram channels  
- 🤖 **AI-Powered Summaries**: Automatic LLM-generated summaries of news messages
- 📤 **Auto-Forward Summaries**: Send summaries to a designated SINK_CHANNEL automatically
- 🔐 **Secure Sessions**: In-memory session storage with no sensitive data written to disk
- 📺 **Smart Channel Management**: Easy channel selection with visual indicators
- 💾 **Intelligent Caching**: Efficient channel caching to minimize API calls
- 📋 **Centralized Logging**: All activity logged to `logs.txt` for easy debugging
- 🐳 **Docker Ready**: Full Docker support for easy deployment
- ⚡ **Async Architecture**: High-performance async/await based design

## 🚀 Quick Start

### 1. Get Telegram API Credentials

1. Visit [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your phone number
3. Create a new application
4. Save your `API ID` and `API Hash`

### 2. Setup & Run

```bash
# Clone the repository
git clone <repository-url>
cd news_reader

# Run the interactive setup script
./setup.sh

# Choose setup method:
# 1) Docker (recommended for production)
# 2) Python Virtual Environment (recommended for development)

# Configure your credentials
nano .env
```

### 3. Configure Environment

Create a `.env` file with your Telegram credentials:

```env
# Required: Your Telegram API credentials
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890

# Optional: OpenAI API for LLM summarization
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL_NAME=gpt-3.5-turbo

# Optional: Channel for automatic summary forwarding
# Use channel ID (e.g., -1001234567890) or username (e.g., @your_channel)
SINK_CHANNEL=@your_summary_channel
```

### 4. Launch the Application

**Virtual Environment (Recommended for Development):**
```bash
./run_venv.sh
```

**Docker (Recommended for Production):**
```bash
docker-compose up news-reader
```

The app will guide you through:
- 📱 Phone verification (first run only)
- 🔐 Two-factor authentication (if enabled)
- 🎨 Modern terminal interface launch

## 🎨 Using the Modern Interface

The News Reader features a beautiful terminal-based graphical interface powered by Textual. Navigate with keyboard shortcuts or mouse clicks!

### 📋 Main Menu

After launching, you'll see the main menu with these options:

- **1. Application Status** - View connection info and monitoring stats
- **2. View Channels** - Browse your Telegram channels with monitoring indicators  
- **3. Monitoring** - Configure which channels to monitor
- **4. View Logs** - See real-time monitoring activity
- **5. Reload Configuration** - Refresh settings
- **Q. Quit Application** - Exit the app

### ⌨️ Keyboard Shortcuts

- **Number keys (1-5)** - Quick menu navigation
- **Q** - Quit from any screen
- **Escape** - Go back to previous screen
- **U** - Update channels (in Channels screen)
- **S** - Setup monitoring (in Monitoring screen)
- **C** - Copy channel ID to clipboard
- **Ctrl+S** - Save configuration
- **Ctrl+A/N** - Select all/none (in setup screens)

### 📺 Channel Management

1. **View Channels** → See all your Telegram channels
2. **Press 'U'** → Update from Telegram API
3. **Navigate with arrows** → Select channels
4. **Press 'C'** → Copy channel ID to clipboard

### 📡 Setting Up Monitoring

1. **Monitoring** → **Press 'S'** → Setup screen opens
2. **Check/uncheck channels** → Select what to monitor
3. **Ctrl+S** → Save configuration
4. **Real-time monitoring begins automatically**

### 📋 Real-time Logs

- **View Logs** → See live monitoring activity
- **Press 'C'** → Clear log history
- Messages appear instantly as they're received

> **💡 Pro Tip**: All activity is automatically logged to `logs.txt` for debugging and review.

### 📤 SINK_CHANNEL Auto-Forwarding

The News Reader can automatically forward AI-generated summaries to a designated Telegram channel:

**Setup:**
1. **Create or choose a channel** where summaries will be sent
2. **Add the bot as admin** to the target channel (with message sending permissions)
3. **Configure SINK_CHANNEL** in your `.env` file:
   ```env
   # Use channel ID (recommended)
   SINK_CHANNEL=-1001234567890
   
   # Or use channel username
   SINK_CHANNEL=@your_summary_channel
   ```

**How it works:**
- When a message is received from monitored channels
- If LLM summarization is enabled and successful
- The summary is automatically formatted and sent to SINK_CHANNEL
- Includes source channel, sender, timestamp, and formatted summary

**Message Format:**
```
📰 News Summary

Source: Original Channel Name
From: Sender Name  
Time: 2024-01-15 14:30:25

Summary:
[AI-generated summary of the original message]

---
Generated by News Reader Bot
```

## 🏗️ Architecture

```
news_reader/
├── news_reader/              # Main application package
│   ├── app.py               # Core application controller
│   ├── main.py              # Application entry point
│   ├── textual_cli_task.py  # Modern Textual-based UI
│   ├── monitoring_task.py   # Real-time channel monitoring
│   ├── config.py            # Configuration management
│   ├── db_client.py         # Database operations
│   └── logging_config.py    # Centralized logging setup
├── logs.txt                 # Application logs
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker configuration
├── setup.sh                 # Interactive setup script
└── run_venv.sh             # Virtual environment launcher
```

### Key Components

- **🎨 Textual UI** (`textual_cli_task.py`) - Modern terminal interface with screens, menus, and keyboard shortcuts
- **📡 Monitoring** (`monitoring_task.py`) - Async background monitoring of Telegram channels
- **🗄️ Database** (`db_client.py`) - Local JSON database with channel caching and configuration storage
- **📋 Logging** (`logging_config.py`) - Centralized logging to `logs.txt` with no console output interference

## 🔧 Troubleshooting

### Common Issues

**❌ Authorization Problems**
- Check your API credentials in `.env`
- Use international phone format: `+1234567890`
- Restart the app to re-authenticate

**❌ No Channels Showing**
- Press 'U' in the Channels screen to update from Telegram API
- Ensure you're a member of the channels you want to monitor

**❌ Monitoring Not Working**
- Check **View Logs** screen for error messages
- Verify channels are selected in **Monitoring** → **Setup**
- Review `logs.txt` for detailed debugging info

### 📋 Debug Information

All application activity is logged to `logs.txt` in the project root. Check this file for detailed error messages and debugging information.

## 🔒 Security

- 🔐 Sessions stored in memory only (no disk storage)
- 🚫 Never commit `.env` files to version control  
- 🔑 Use strong 2FA passwords
- 🔄 Re-authentication required on each restart (security feature)

## 📄 License

This project is provided as-is for educational and personal use.
