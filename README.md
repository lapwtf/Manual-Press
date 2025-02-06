# Discord AutoPress

A powerful Discord automation tool with realistic typing simulation, customizable message handling, and anti-AFK features.

## 🚀 Features

- 🤖 Realistic typing simulation with variable WPM
- 📝 Multiple wordlist modes for different messaging styles
- 🎯 Prefix and suffix support with mention handling
- 🔄 Anti-AFK response system
- 💬 Group chat name changer
- ⚡ Browser-based automation for reliability

## ⚙️ Setup

1. Install Python 3.8 or higher
2. Install required dependencies:
```bash
pip install discord.py selenium colorama aiohttp
```
3. Download ChromeDriver matching your Chrome version from [ChromeDriver Downloads](https://sites.google.com/chromium.org/driver/)
4. Place `chromedriver.exe` in the same directory as the script
5. Create a `config.json` file with your Discord token:
```json
{
    "token": "your_discord_token_here"
}
```

## 📚 Commands Guide

### Basic Commands

1. **Set Channel and User Settings**
```bash
set -ci [channel_id] -ui [user_id] -dl [delay]
```
- `channel_id`: Target channel ID
- `user_id`: User ID for mentions
- `delay`: Message delay (e.g., "0.5-0.8")

2. **Start Browser Mode**
```bash
kill -srv [server_id] -ci [channel_id] -wpm [speed]
```
- `server_id`: Discord server ID
- `channel_id`: Channel ID
- `wpm`: Typing speed in words per minute

### Advanced Features

#### Message Customization
```bash
kill -srv [server_id] -ci [channel_id] -wpm [speed] -prefix [prefix] -suffix [suffix]
```

Examples:
1. Simple text:
```bash
kill -srv 123456789 -ci 987654321 -wpm 60 -prefix "Hello" -suffix "Goodbye"
```

2. With mentions:
```bash
kill -srv 123456789 -ci 987654321 -wpm 60 -prefix "<@userid>" -suffix "<@userid>"
```

3. Mixed format:
```bash
kill -srv 123456789 -ci 987654321 -wpm 60 -prefix "Hey <@userid>" -suffix "from <@userid>"
```

#### Group Chat Name Changer
```bash
kill -gc
```

#### Skull Mode (React with ☠️)
```bash
kill -skull
```

#### Line Override
```bash
kill -ln [line_number]
```

#### Send Direct Message
```bash
-sd [message]
```

## 🎮 Wordlist Modes

The tool supports 4 different wordlist modes:
1. Logical (Mode 1)
2. Beef (Mode 2)
3. Yap (Mode 3)
4. Ragebait (Mode 4)

Each mode uses different wordlists from the `wordlists/` directory.

## ⚠️ Anti-AFK System

The tool automatically responds to:
- AFK checks
- Client checks
- Custom say commands
- Messages in quotes

Response time and cooldown are configurable in the anti-afk_settings.

## 🔧 Advanced Configuration

### Settings Dictionary
```python
settings = {
    'channel_id': None,      # Target channel
    'user_id': None,         # User for mentions
    'delay': '0.5-0.8',      # Message delay range
    'skull_mode': False,     # Skull reaction mode
    'name_replacement': None, # Name replacement in messages
    'server_id': None,       # Server ID for browser mode
    'wpm': None,            # Typing speed
    'prefix': None,         # Message prefix
    'suffix': None          # Message suffix
}
```

## 🛑 Stopping the Tool

To stop the tool:
1. Type `quit` in the console
2. Or use Ctrl+C to force stop

## 📋 Tips & Tricks

1. **Optimal WPM Settings**
   - For realistic typing: 40-80 WPM
   - For faster operation: 100-150 WPM

2. **Delay Settings**
   - Format: "min-max" (e.g., "0.5-0.8")
   - Lower values = faster messages
   - Higher values = more human-like

3. **Browser Mode Benefits**
   - More reliable than API mode
   - Better anti-detection
   - Realistic typing simulation

## ⚠️ Important Notes

1. Keep ChromeDriver updated with your Chrome browser version
2. Don't set WPM too high to avoid detection
3. Use reasonable delays between messages
4. Keep your Discord token private
5. Don't abuse the tool to avoid account restrictions

## 🤝 Contributing

Feel free to fork and submit pull requests. For major changes, open an issue first.

## 📜 License

This project is for educational purposes only. Use responsibly and at your own risk.
