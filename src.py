import discord
from discord.ext import commands
import os
import json
from datetime import datetime
import random
import asyncio
import aiohttp
import time
import requests
import colorama
from colorama import Fore, Back, Style
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import string

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='+', self_bot=True, intents=intents)
bot.remove_command('help')

command_queue = asyncio.Queue()
active_task = None
current_active_mode = 2  

mode_positions = {
    1: 0,
    2: 0,
    3: 0,
    4: 0
}

def get_config_token():
    with open('config.json') as f:
        config = json.load(f)
    return config['token']

settings = {
    'channel_id': None,
    'user_id': None,
    'delay': '0.5-0.8',
    'skull_mode': False,
    'name_replacement': None,
    'line_override': None,
    'server_id': None,
    'wpm': None,
    'prefix': None,
    'suffix': None
}

async def send_messages_from_wordlist(mode):
    global active_task, mode_positions
    try:
        if not settings['channel_id']:
            print("Error: Channel ID must be set first")
            print("Use: kill -ci [channel_id] -ui [user_id] -dl [delay]")
            return

        channel_id = settings['channel_id']
        user_id = settings['user_id']
        current_mode = mode
        print(f"Starting mode {mode}...")
        
        messages_sent = 0
        stop_requested = False

        while not command_queue.empty():
            _ = command_queue.get_nowait()

        while True:
            try:
                if not command_queue.empty():
                    cmd = command_queue.get_nowait()
                    if isinstance(cmd, str) and cmd.startswith('stop'):
                        stop_requested = True
            except asyncio.QueueEmpty:
                pass

            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': get_config_token(),
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }


                wordlist_path = {
                    1: "wordlists/logical.txt",
                    2: "wordlists/beef.txt",
                    3: "wordlists/yap.txt",
                    4: "wordlists/ragebait.txt"
                }.get(current_mode)

                with open(wordlist_path, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]

                if settings['line_override'] is not None:
                    if 0 <= settings['line_override'] < len(lines):
                        mode_positions[current_mode] = settings['line_override']
                        print(f"Starting from line: {settings['line_override']}")
                        settings['line_override'] = None
                    else:
                        print(f"Warning: Line number {settings['line_override']} is out of range. Using current position.")
                        settings['line_override'] = None

                current_position = mode_positions.get(current_mode, 0)

                for i in range(current_position, len(lines)):
                    if stop_requested and messages_sent >= 5:
                        return

                    line = lines[i]
                    if '{name}' in line or '{UPname}' in line:
                        if settings['name_replacement']:
                            message = line.replace('{name}', settings['name_replacement'])
                            message = message.replace('{UPname}', settings['name_replacement'].upper())
                        else:
                            continue
                    else:
                        message = line

                    if '{mention}' in message and not user_id:
                        continue

                    message = message.replace('\\n', '\n')
                    message = message.replace('{mention}', f'<@{user_id}>') if user_id else message
                    
                    if settings.get('prefix'):
                        prefix = settings['prefix'].strip()
                        if prefix.startswith('<@') and prefix.endswith('>'):
                            user_to_mention = prefix[2:-1]
                            if user_to_mention.startswith('!'):
                                user_to_mention = user_to_mention[1:]
                            prefix = f'<@{user_to_mention}>'
                        elif ' ' in prefix:
                            prefix_parts = []
                            for part in prefix.split():
                                if part.startswith('<@') and part.endswith('>'):
                                    user_to_mention = part[2:-1]
                                    if user_to_mention.startswith('!'):
                                        user_to_mention = user_to_mention[1:]
                                    prefix_parts.append(f'<@{user_to_mention}>')
                                else:
                                    prefix_parts.append(part)
                            prefix = ' '.join(prefix_parts)
                        message = f"{prefix} {message}"

                    if settings.get('suffix'):
                        suffix = settings['suffix'].strip()
                        if suffix.startswith('<@') and suffix.endswith('>'):
                            user_to_mention = suffix[2:-1]
                            if user_to_mention.startswith('!'):
                                user_to_mention = user_to_mention[1:]
                            suffix = f'<@{user_to_mention}>'
                        elif ' ' in suffix:
                            suffix_parts = []
                            for part in suffix.split():
                                if part.startswith('<@') and part.endswith('>'):
                                    user_to_mention = part[2:-1]
                                    if user_to_mention.startswith('!'):
                                        user_to_mention = user_to_mention[1:]
                                    suffix_parts.append(f'<@{user_to_mention}>')
                                else:
                                    suffix_parts.append(part)
                            suffix = ' '.join(suffix_parts)
                        message = f"{message} {suffix}"

                    message = ' '.join(message.split())

                    if '{mention}' in message:
                        current_position += 1
                        continue

                    payload = {'content': message}
                    
                    async with session.post(
                        f'https://discord.com/api/v9/channels/{channel_id}/messages',
                        headers=headers,
                        json=payload
                    ) as resp:
                        if resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 5)
                            await asyncio.sleep(float(retry_after))
                            continue
                        elif resp.status not in [200, 201]:
                            continue
                        else:
                            mode_positions[current_mode] = i + 1
                            messages_sent += 1
                            if settings['skull_mode']:
                                message_data = await resp.json()
                                message_id = message_data['id']
                                await session.put(
                                    f'https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/☠️/@me',
                                    headers=headers
                                )

                    delay = settings['delay']
                    if '-' in str(delay):
                        min_delay, max_delay = map(float, delay.split('-'))
                        delay_time = random.uniform(min_delay, max_delay)
                    else:
                        delay_time = float(delay)
                    
                    await asyncio.sleep(delay_time)

                    if messages_sent >= 5 and settings['line_override'] is not None:
                        mode_positions[current_mode] = settings['line_override']
                        print(f"Next sequence will start from line: {mode_positions[current_mode]}")
                        settings['line_override'] = None
                        return

                    if mode_positions[current_mode] >= len(lines):
                        mode_positions[current_mode] = 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())

async def change_groupchat_names(mode):
    global active_task, mode_positions
    try:
        if not settings['channel_id']:
            print("Error: Channel ID must be set first")
            print("Use: kill -ci [channel_id] -ui [user_id] -dl [delay]")
            return

        channel_id = settings['channel_id']
        current_mode = mode
        print(f"Starting group chat name changes with mode {mode}...")
        
        messages_sent = 0
        stop_requested = False

        while not command_queue.empty():
            _ = command_queue.get_nowait()

        while True:
            try:
                if not command_queue.empty():
                    cmd = command_queue.get_nowait()
                    if isinstance(cmd, str) and cmd.startswith('stop'):
                        stop_requested = True
            except asyncio.QueueEmpty:
                pass

            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': get_config_token(),
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }

                wordlist_path = {
                    1: "wordlists/logical.txt",
                    2: "wordlists/beef.txt",
                    3: "wordlists/yap.txt",
                    4: "wordlists/ragebait.txt"
                }.get(current_mode)

                with open(wordlist_path, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip() and '{mention}' not in line]

                current_position = mode_positions.get(current_mode, 0)

                for i in range(current_position, len(lines)):
                    if stop_requested and messages_sent >= 5:
                        return

                    line = lines[i]
                    name = line.replace('\\n', ' ')
                    
                    payload = {'name': name}
                    
                    async with session.patch(
                        f'https://discord.com/api/v9/channels/{channel_id}',
                        headers=headers,
                        json=payload
                    ) as resp:
                        if resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 5)
                            await asyncio.sleep(float(retry_after))
                            continue
                        elif resp.status not in [200, 201]:
                            continue
                        else:
                            mode_positions[current_mode] = i + 1

                    delay = settings['delay']
                    if '-' in str(delay):
                        min_delay, max_delay = map(float, delay.split('-'))
                        delay_time = random.uniform(min_delay, max_delay)
                    else:
                        delay_time = float(delay)
                    
                    await asyncio.sleep(delay_time)
                    messages_sent += 1

                    if mode_positions[current_mode] >= len(lines):
                        mode_positions[current_mode] = 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())

def calculate_typing_delay(word, base_wpm):
    base_cps = (base_wpm * 5) / 60  
    
    length_factor = len(word) / 5 
    complexity_factor = 1.0
    
    if any(c in string.punctuation for c in word):
        complexity_factor *= 1.2
    if any(c.isupper() for c in word):
        complexity_factor *= 1.1
    if any(c.isdigit() for c in word):
        complexity_factor *= 1.15
        
    variation = random.uniform(0.85, 1.15)
    
    char_delay = (1 / base_cps) * complexity_factor * variation
    return char_delay * length_factor

async def simulate_realistic_typing(element, text, wpm):
    words = text.split()
    
    for i, word in enumerate(words):
        for char in word:
            element.send_keys(char)
            char_delay = calculate_typing_delay(word, wpm) / len(word)
            await asyncio.sleep(char_delay)
        
        if i < len(words) - 1:
            element.send_keys(Keys.SPACE)
            if word[-1] in '.!?':
                await asyncio.sleep(random.uniform(0.3, 0.5))
            else:
                await asyncio.sleep(random.uniform(0.1, 0.2))

async def send_messages_with_browser(mode):
    global active_task, mode_positions
    driver = None
    
    while True:  
        try:
            if not settings['channel_id'] or not settings['server_id']:
                print("Error: Both Server ID and Channel ID must be set")
                print("Use: kill -srv [server_id] -ci [channel_id] -wpm [speed]")
                return

            if driver:
                try:
                    driver.quit()
                except:
                    pass
                    
            current_dir = os.path.dirname(os.path.abspath(__file__))
            user_data_dir = os.path.join(current_dir, "chrome_data")
            if os.path.exists(user_data_dir):
                import shutil
                try:
                    shutil.rmtree(user_data_dir)
                except:
                    pass
            os.makedirs(user_data_dir, exist_ok=True)

            chrome_options = Options()
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-background-mode")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--window-position=0,0")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-features=RendererCodeIntegrity")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-site-isolation-trials")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-application-cache")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--aggressive-cache-discard")
            chrome_options.add_argument("--disable-cache")
            chrome_options.add_argument("--disable-network-throttling")
            chrome_options.add_argument("--dns-prefetch-disable=false")
            chrome_options.add_argument('--enable-features=NetworkServiceInProcess')
            chrome_options.add_argument("--force-gpu-mem-available-mb=1024")
            chrome_options.add_argument("--disk-cache-size=1")
            chrome_options.page_load_strategy = 'eager'
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("detach", True)
            
            prefs = {
                "protocol_handler": {
                    "excluded_schemes": {
                        "discord": True
                    }
                },
                "protocol_handler.excluded_schemes": {
                    "discord": True
                },
                "custom_handlers": {
                    "enabled": False,
                    "registered_protocol_handlers": []
                },
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.protocol_handlers": 2,
                "profile.content_settings.exceptions.protocol_handlers": {},
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            chromedriver_path = os.path.join(current_dir, "chromedriver.exe")
            
            if not os.path.exists(chromedriver_path):
                print("ChromeDriver not found in current directory!")
                print("Please download ChromeDriver from: https://sites.google.com/chromium.org/driver/")
                print("And place chromedriver.exe in the same directory as this script")
                return
                
            print("Initializing ChromeDriver...")
            service = webdriver.ChromeService(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            wait = WebDriverWait(driver, 20)  

            driver.maximize_window()
            driver.set_window_position(0, 0)
            driver.set_window_size(1920, 1080)

            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Logging in with token...")
            token = get_config_token()
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    driver.get("https://discord.com/login")
                    await asyncio.sleep(2)
                    
                    script = """
                        window.webpackChunkdiscord_app.push([[Math.random()], {}, (req) => {
                            for (const m of Object.keys(req.c).map((x) => req.c[x].exports).filter((x) => x)) {
                                if (m.default && m.default.setToken !== undefined) {
                                    m.default.setToken('%s');
                                    return;
                                }
                                if (m.setToken !== undefined) {
                                    m.setToken('%s');
                                    return;
                                }
                            }
                        }]);
                        window.location.reload();
                    """ % (token, token)
                    
                    driver.execute_script(script)
                    await asyncio.sleep(3)
                    
                    print(f"Navigating to Discord channel...")
                    discord_url = f"https://discord.com/channels/{settings['server_id']}/{settings['channel_id']}"
                    driver.get(discord_url)
                    
                    selectors = [
                        '[role="textbox"]',
                        'div[data-slate-editor="true"]',
                        '#message-input',
                        'div[contenteditable="true"]',
                        'div[class*="slateTextArea"]'
                    ]
                    
                    message_input = None
                    for selector in selectors:
                        try:
                            message_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            if message_input:
                                print("Found message input!")
                                break
                        except:
                            continue
                    
                    if message_input:
                        break
                        
                    retry_count += 1
                    print(f"Retry {retry_count}/{max_retries}")
                    
                except Exception as e:
                    print(f"Error during setup: {str(e)}")
                    retry_count += 1
                    await asyncio.sleep(5)
            
            if not message_input:
                raise Exception("Failed to find message input after retries")

            messages_sent = 0
            stop_requested = False
            current_position = mode_positions.get(mode, 0)

            while not command_queue.empty():
                _ = command_queue.get_nowait()

            while True:
                try:
                    if not command_queue.empty():
                        cmd = command_queue.get_nowait()
                        if isinstance(cmd, str) and cmd.startswith('stop'):
                            stop_requested = True
                except asyncio.QueueEmpty:
                    pass

                if settings['user_id'] and settings['channel_id']:
                    headers = {
                        'Authorization': get_config_token(),
                        'Content-Type': 'application/json'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f'https://discord.com/api/v9/channels/{settings["channel_id"]}/messages?limit=5',
                            headers=headers
                        ) as resp:
                            if resp.status == 200:
                                messages = await resp.json()
                                for msg in messages:
                                    if str(msg['author']['id']) == settings['user_id']:
                                        content = msg['content']
                                        content = ' '.join([word for word in content.split() if not word.startswith('<@') and not word.endswith('>')])
                                        content = content.lower()
                                        
                                        check_phrases = ['afk check say', 'client check say', 'check say']
                                        for phrase in check_phrases:
                                            if phrase in content:
                                                mode_positions[mode] = current_position
                                                
                                                response_text = content.split("say", 1)[1].strip()

                                                message_input = driver.find_element(By.CSS_SELECTOR, '[role="textbox"]')
                                                
                                                words = response_text.split()
                                                total_words = len(words)
                                                wpm = float(settings['wpm'])
                                                seconds_per_word = 60.0 / wpm
                                                time_per_word = seconds_per_word / total_words

                                                for word in words:
                                                    chars_in_word = len(word)
                                                    delay_per_char = time_per_word / chars_in_word
                                                    
                                                    for char in word:
                                                        message_input.send_keys(char)
                                                        await asyncio.sleep(delay_per_char)
                                                    message_input.send_keys(Keys.SPACE)
                                                
                                                message_input.send_keys(Keys.RETURN)
                                                await asyncio.sleep(0.1)
                                                
                                                await asyncio.sleep(1.0)
                                                break

                wordlist_path = {
                    1: "wordlists/logical.txt",
                    2: "wordlists/beef.txt",
                    3: "wordlists/yap.txt",
                    4: "wordlists/ragebait.txt"
                }.get(mode)

                with open(wordlist_path, 'r') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]

                if current_position < len(lines):
                    line = lines[current_position]
                    if '{name}' in line or '{UPname}' in line:
                        if settings['name_replacement']:
                            message = line.replace('{name}', settings['name_replacement'])
                            message = message.replace('{UPname}', settings['name_replacement'].upper())
                        else:
                            current_position += 1
                            continue
                    else:
                        message = line

                    if settings.get('prefix'):
                        prefix = settings['prefix'].strip()
                        if prefix.startswith('<@') and prefix.endswith('>'):
                            user_to_mention = prefix[2:-1]
                            if user_to_mention.startswith('!'):
                                user_to_mention = user_to_mention[1:]
                            prefix = f'<@{user_to_mention}>'
                        elif ' ' in prefix:
                            prefix_parts = []
                            for part in prefix.split():
                                if part.startswith('<@') and part.endswith('>'):
                                    user_to_mention = part[2:-1]
                                    if user_to_mention.startswith('!'):
                                        user_to_mention = user_to_mention[1:]
                                    prefix_parts.append(f'<@{user_to_mention}>')
                                else:
                                    prefix_parts.append(part)
                            prefix = ' '.join(prefix_parts)
                        message = f"{prefix} {message}"

                    if settings.get('suffix'):
                        suffix = settings['suffix'].strip()
                        if suffix.startswith('<@') and suffix.endswith('>'):
                            user_to_mention = suffix[2:-1]
                            if user_to_mention.startswith('!'):
                                user_to_mention = user_to_mention[1:]
                            suffix = f'<@{user_to_mention}>'
                        elif ' ' in suffix:
                            suffix_parts = []
                            for part in suffix.split():
                                if part.startswith('<@') and part.endswith('>'):
                                    user_to_mention = part[2:-1]
                                    if user_to_mention.startswith('!'):
                                        user_to_mention = user_to_mention[1:]
                                    suffix_parts.append(f'<@{user_to_mention}>')
                                else:
                                    suffix_parts.append(part)
                            suffix = ' '.join(suffix_parts)
                        message = f"{message} {suffix}"

                    message = ' '.join(message.split())

                    if '{mention}' in message:
                        current_position += 1
                        continue

                    message_input = None
                    selectors = [
                        '[role="textbox"]',
                        'div[data-slate-editor="true"]',
                        '#message-input',
                        'div[contenteditable="true"]',
                        'div[class*="slateTextArea"]'
                    ]
                    
                    for selector in selectors:
                        try:
                            message_input = driver.find_element(By.CSS_SELECTOR, selector)
                            if message_input and message_input.is_displayed():
                                break
                        except:
                            continue
                    
                    if not message_input:
                        print("Could not find message input. Please make sure you're logged in and have access to the channel.")
                        driver.quit()
                        return

                    await simulate_realistic_typing(message_input, message, float(settings['wpm']))
                    message_input.send_keys(Keys.RETURN)
                    current_position += 1
                    messages_sent += 1
                    await asyncio.sleep(0.1)

                    if current_position >= len(lines):
                        current_position = 0

                mode_positions[mode] = current_position

                if stop_requested and messages_sent >= 5:
                    driver.quit()
                    return

        except Exception as e:
            print(f"Major error occurred: {str(e)}")
            print("Restarting browser session...")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            await asyncio.sleep(5)
            continue

anti_afk_settings = {
    'last_response_time': 0,
    'cooldown': 0.5,
    'last_message_id': None,
    'cached_messages': {},
    'min_delay': 1.5,
    'max_delay': 3.5
}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if not settings['channel_id'] or str(message.channel.id) != settings['channel_id']:
        return

    current_time = time.time()
    if current_time - anti_afk_settings['last_response_time'] < anti_afk_settings['cooldown']:
        return

    try:
        headers = {
            'Authorization': get_config_token(),
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        params = {'after': anti_afk_settings['last_message_id']} if anti_afk_settings['last_message_id'] else {'limit': 1}
        response = requests.get(
            f"https://discord.com/api/v9/channels/{message.channel.id}/messages",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            messages = response.json()
            
            for msg in reversed(messages):
                if msg['id'] not in anti_afk_settings['cached_messages']:
                    anti_afk_settings['cached_messages'][msg['id']] = True
                    
                    if msg['author']['id'] == bot.user.id or (settings['user_id'] and msg['author']['id'] != settings['user_id']):
                        continue

                    content = msg.get('content', '').lower()
                    original_content = msg.get('content', '')
                    response_text = None

                    if 'afk check' in content or 'say' in content or '"' in content or "'" in content:
                        if '"' in original_content:
                            try:
                                parts = original_content.split('"')
                                for i in range(1, len(parts), 2):
                                    if parts[i].strip():
                                        response_text = parts[i]
                                        break
                            except:
                                pass

                        if not response_text and "'" in original_content:
                            try:
                                parts = original_content.split("'")
                                for i in range(1, len(parts), 2):
                                    if parts[i].strip():
                                        response_text = parts[i]
                                        break
                            except:
                                pass

                        if not response_text and 'say' in content:
                            try:
                                after_say = original_content.lower().split('say', 1)[1].strip()
                                if after_say:
                                    response_text = after_say
                            except:
                                pass

                        if not response_text and 'afk check' in content:
                            response_text = original_content

                        if response_text:
                            delay = random.uniform(anti_afk_settings['min_delay'], anti_afk_settings['max_delay'])
                            await asyncio.sleep(delay)
                            try:
                                payload = {
                                    'content': response_text,
                                    'message_reference': {
                                        'message_id': str(msg['id']),
                                        'channel_id': str(message.channel.id),
                                        'guild_id': msg.get('guild_id')
                                    }
                                }

                                async with aiohttp.ClientSession() as session:
                                    async with session.post(
                                        f'https://discord.com/api/v9/channels/{message.channel.id}/messages',
                                        headers=headers,
                                        json=payload
                                    ) as resp:
                                        if resp.status == 429:
                                            retry_after = (await resp.json()).get('retry_after', 5)
                                            await asyncio.sleep(float(retry_after))
                                        anti_afk_settings['last_response_time'] = current_time

                            except Exception as e:
                                print(f"Error in anti-AFK response: {e}")

                    anti_afk_settings['last_message_id'] = msg['id']

    except Exception as e:
        print(f"Error checking messages: {e}")

@bot.event
async def on_ready():
    global active_task, current_active_mode
    user = bot.user
    nitro_status = "Premium Nitro" if user.premium_type == 2 else "Nitro Classic" if user.premium_type == 1 else "No Nitro"
    
    print(f"""
{Fore.RED}

                    .▄▄ ·        ▄▄· ▪   ▄▄▄· ▄▄▌      ▐▄• ▄     ▄▄▌   ▄▄▄·  ▄▄▄· ▄▄▄· ▄· ▄▌
                    ▐█ ▀. ▪     ▐█ ▌▪██ ▐█ ▀█ ██•       █▌█▌▪    ██•  ▐█ ▀█ ▐█ ▄█▐█ ▄█▐█▪██▌
                    ▄▀▀▀█▄ ▄█▀▄ ██ ▄▄▐█·▄█▀▀█ ██▪       ·██·     ██▪  ▄█▀▀█  ██▀· ██▀·▐█▌▐█▪
                    ▐█▄▪▐█▐█▌.▐▌▐███▌▐█▌▐█ ▪▐▌▐█▌▐▌    ▪▐█·█▌    ▐█▌▐▌▐█ ▪▐▌▐█▪·•▐█▪·• ▐█▀·.
                     ▀▀▀▀  ▀█▄▀▪·▀▀▀ ▀▀▀ ▀  ▀ .▀▀▀     •▀▀ ▀▀    .▀▀▀  ▀  ▀ .▀   .▀     ▀ • 

{Fore.RESET}
""")
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("-" * 40)
    print(f"User: {user.name}#{user.discriminator}")
    print(f"Nitro: {nitro_status}")
    print("-" * 40)

    loop = asyncio.get_event_loop()

    while True:
        command = await loop.run_in_executor(None, input, "srv > ")
        
        try:
            if ' -sd ' in command:
                if not settings['channel_id']:
                    print("Error: Channel ID must be set first")
                    print("Use: kill -ci [channel_id] -ui [user_id] -dl [delay]")
                    continue
                
                message = command.split(' -sd ')[1]
                
                async with aiohttp.ClientSession() as session:
                    headers = {
                        'Authorization': get_config_token(),
                        'Content-Type': 'application/json',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    payload = {'content': message}
                    
                    async with session.post(
                        f'https://discord.com/api/v9/channels/{settings["channel_id"]}/messages',
                        headers=headers,
                        json=payload
                    ) as resp:
                        if resp.status == 429:
                            retry_after = (await resp.json()).get('retry_after', 5)
                            print(f"Rate limited. Waiting {retry_after} seconds...")
                            await asyncio.sleep(float(retry_after))
                        elif resp.status not in [200, 201]:
                            print(f"Error sending message: {resp.status}")
                        else:
                            print("Message sent successfully")
                continue

            if command.lower() == 'quit':
                if active_task:
                    await command_queue.put('stop')
                    for task in active_task:
                        task.cancel()
                await bot.close()
                break

            if command.startswith('set'):
                try:
                    params = command.split()
                    for i, param in enumerate(params):
                        if param == '-ci':
                            settings['channel_id'] = params[i + 1]
                            print(f"Channel ID set to: {params[i + 1]}")
                        elif param == '-ui':
                            settings['user_id'] = params[i + 1]
                            print(f"User ID set to: {params[i + 1]}")
                        elif param == '-dl':
                            settings['delay'] = params[i + 1]
                            print(f"Delay set to: {params[i + 1]}")
                    
                    print("\nCurrent settings:")
                    print(f"Channel ID: {settings['channel_id']}")
                    print(f"User ID: {settings['user_id']}")
                    print(f"Delay: {settings['delay']}")

                except Exception as e:
                    print(f"Error updating settings: {e}")
                    print("Usage: set -ci [channel_id] -ui [user_id] -dl [delay]")

            elif command.startswith('kill'):
                try:
                    params = command.split()

                    has_server_id = any(param == '-srv' for param in params)
                    has_wpm = any(param == '-wpm' for param in params)

                    for i, param in enumerate(params):
                        if param == '-srv':
                            settings['server_id'] = params[i + 1]
                            print(f"Server ID set to: {params[i + 1]}")
                        elif param == '-wpm':
                            settings['wpm'] = params[i + 1]
                            print(f"WPM set to: {params[i + 1]}")
                        elif param == '-ci':
                            settings['channel_id'] = params[i + 1]
                            print(f"Channel ID updated to: {params[i + 1]}")
                        elif param == '-ui':
                            settings['user_id'] = params[i + 1]
                            print(f"User ID updated to: {params[i + 1]}")
                        elif param == '-dl':
                            settings['delay'] = params[i + 1]
                            print(f"Delay updated to: {params[i + 1]}")
                        elif param == '-na':
                            settings['name_replacement'] = params[i + 1]
                            print(f"Name replacement set to: {params[i + 1]}")
                        elif param == '-prefix':
                            settings['prefix'] = params[i + 1]
                            print(f"Prefix set to: {params[i + 1]}")
                        elif param == '-suffix':
                            settings['suffix'] = params[i + 1]
                            print(f"Suffix set to: {params[i + 1]}")

                    if has_server_id and has_wpm:
                        print("Starting browser mode...")
                        if active_task and isinstance(active_task, list):
                            print("Stopping previous mode...")
                            await command_queue.put('stop')
                            for task in active_task:
                                task.cancel()
                            active_task = None
                            await asyncio.sleep(1.0)
                        
                        active_task = [asyncio.create_task(send_messages_with_browser(current_active_mode))]
                        continue

                    if command == 'kill -skull':
                        settings['skull_mode'] = not settings.get('skull_mode', False)
                        status = "enabled" if settings['skull_mode'] else "disabled"
                        print(f"Skull reaction mode {status}")
                        continue

                    if command == 'kill -gc':
                        if not settings['channel_id']:
                            print("Error: Channel ID must be set first")
                            print("Use: kill -ci [channel_id] -ui [user_id] -dl [delay]")
                            continue
                            
                        print("Starting group chat name changer...")

                        if active_task and isinstance(active_task, list):
                            print("Stopping previous mode...")
                            await command_queue.put('stop')
                            for task in active_task:
                                task.cancel()
                                try:
                                    await task
                                except asyncio.CancelledError:
                                    pass
                            active_task = None
                            await asyncio.sleep(1.0)

                        active_task = [asyncio.create_task(change_groupchat_names(current_active_mode))]
                        continue

                    params = command.split()

                    for i, param in enumerate(params):
                        if param == '-ln':
                            try:
                                line_num = int(params[i + 1])
                                settings['line_override'] = line_num

                                if active_task and isinstance(active_task, list):
                                    for task in active_task:
                                        task.cancel()
                                        try:
                                            await task
                                        except asyncio.CancelledError:
                                            pass
                                    active_task = None
                                    await asyncio.sleep(1.0)

                                active_task = [asyncio.create_task(send_messages_from_wordlist(current_active_mode))]
                                print(f"Starting new sequence from line: {line_num}")
                                continue
                            except (ValueError, IndexError):
                                print("Invalid line number format. Use: kill -ln [number]")
                                continue

                    if command.startswith('kill -ln ') and len(command.split()) == 3:
                        continue

                    for i, param in enumerate(params):
                        if param == '-ci':
                            settings['channel_id'] = params[i + 1]
                            print(f"Channel ID updated to: {params[i + 1]}")
                        elif param == '-ui':
                            settings['user_id'] = params[i + 1]
                            print(f"User ID updated to: {params[i + 1]}")
                        elif param == '-dl':
                            settings['delay'] = params[i + 1]
                            print(f"Delay updated to: {params[i + 1]}")
                        elif param == '-na':
                            settings['name_replacement'] = params[i + 1]
                            print(f"Name replacement set to: {params[i + 1]}")
                        elif param == '-prefix':
                            settings['prefix'] = params[i + 1]
                            print(f"Prefix set to: {params[i + 1]}")
                        elif param == '-suffix':
                            settings['suffix'] = params[i + 1]
                            print(f"Suffix set to: {params[i + 1]}")

                    if command.startswith('kill -na ') and len(command.split()) == 3:
                        continue

                    mode = next((int(params[i + 1]) for i, param in enumerate(params) if param == '-md'), None)
                    if mode:
                        current_active_mode = mode
                        print(f"Regenegade raider")
                        print(f"Channel: {settings['channel_id']}")
                        print(f"Target: {settings['user_id']}")
                        print(f"Mode: {mode}")
                        print(f"Delay: {settings['delay']}")

                        while not command_queue.empty():
                            _ = command_queue.get_nowait()

                        if active_task and isinstance(active_task, list):
                            print("Stopping previous mode...")
                            await command_queue.put('stop')
                            for task in active_task:
                                task.cancel()
                                try:
                                    await task
                                except asyncio.CancelledError:
                                    pass
                            active_task = None
                            await asyncio.sleep(1.0)

                        print(f"Initializing mode {mode}...")
                        active_task = [asyncio.create_task(send_messages_from_wordlist(mode))]
                        print(f"Mode {mode} is now active")

                    elif settings['server_id'] and settings['wpm']:
                        if active_task and isinstance(active_task, list):
                            print("Stopping previous mode...")
                            await command_queue.put('stop')
                            for task in active_task:
                                task.cancel()
                            active_task = None
                            await asyncio.sleep(1.0)
                        
                        active_task = [asyncio.create_task(send_messages_with_browser(current_active_mode))]
                        continue

                except Exception as e:
                    print(f"Error in kill command: {e}")
                    print("Usage: kill -md [mode] -ci [channel_id] -ui [user_id] -dl [delay] -na [name] -prefix [prefix] -suffix [suffix]")
                    active_task = None

            elif command == 'stop' and active_task:
                await command_queue.put('stop')
                for task in active_task:
                    task.cancel()
                active_task = None
                print("Regenegade raider")
            elif command.lower() == 'settings':
                print("\nCurrent settings:")
                print(f"Channel ID: {settings['channel_id']}")
                print(f"User ID: {settings['user_id']}")
                print(f"Delay: {settings['delay']}")
            else:
                print(f"Unknown command: {command}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            print(traceback.format_exc())


token = get_config_token()
bot.run(token, bot=False)