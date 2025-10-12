#!/usr/bin/env python3
"""
News Reader - Main Entry Point
Simple launcher for the unified News Reader application
"""

import sys
import asyncio
from news_reader.app import NewsReaderApp

if __name__ == '__main__':
    app = NewsReaderApp()
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
