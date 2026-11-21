# CIPHER

A personal AI assistant for Termux and Telegram with a cybersecurity core.
It chats like a normal AI, remembers things about you, runs security tools,
manages social media drafts, researches topics, and talks by voice.

## Modes

Switch with /mode <name>. Each mode has its own personality and tool set.

- security: scanner, hash tools, password tools, log analysis, CVE lookup,
  WHOIS, subdomain lookup, SSL checks
- social: captions, hooks, hashtags, content calendars, post scheduler
- chill: jokes, banter, and a friendly listener
- research: Wikipedia lookups with sources

All modes include weather, time, notes, and persistent memory.

## Features

- Natural-language tool calling on any OpenAI-compatible API (Groq by default)
- Persistent memory and notes stored in ~/.cipher/
- Scope guard: scans and certificate checks only run on hosts you add with
  /scope add. Only you can edit the scope, the model cannot.
- Telegram front-end locked to one owner account
- Voice notes in (Whisper speech-to-text) and voice replies out (gTTS)
- Post scheduler: CIPHER messages you the post at the chosen time
- Secrets are redacted from logs and error messages

## Install

    pkg install python git -y
    git clone https://github.com/Denmax3shang/cipher.git cipher_project
    cd cipher_project
    pip install -r requirements.txt

## Configure

Keys are read from environment variables only and are never stored in this repo.

    export LLM_API_KEY="your-key"
    export LLM_MODEL="openai/gpt-oss-120b"
    export LLM_BASE_URL="https://api.groq.com/openai/v1"

Optional:

    STT_MODEL     speech-to-text model (default whisper-large-v3-turbo)
    STT_LANG      transcription language (default en, empty for auto-detect)

Model names change over time. If you get "model not found", check your
provider's model list. Voice input needs a provider that serves Whisper.

## Run in the terminal

    python -m cipher

Commands: /help, /mode, /scope add|remove|list, /voice on|off, /clear, /exit

## Run the Telegram bot

    export TELEGRAM_TOKEN="token-from-botfather"
    export TELEGRAM_OWNER_ID="your-numeric-id"
    python -m cipher.telegram_bot

Message the bot once without an owner ID set and it replies with your ID.
Messages from any other account are ignored. Scheduled posts are delivered
only while the bot is running. To also publish them to a channel, add the bot
as a channel admin and set TELEGRAM_CHANNEL="@yourchannel".

## Project layout

    cipher/
      app.py            terminal interface and slash commands
      telegram_bot.py   Telegram front-end, voice, post delivery
      personality.py    mode prompts
      config.py         settings from environment variables
      core/
        brain.py        LLM calls and tool loop
        memory.py       JSON storage, facts, scope, voice setting
        scheduler.py    scheduled posts
      skills/
        system.py       time, notes, memory
        security.py     scanner, hashes, passwords, header audit
        logs.py         auth and web log analyzer
        cve.py          NVD vulnerability lookup
        recon.py        WHOIS, subdomains, SSL check
        social.py       post scheduling tools
        research.py     Wikipedia lookup
        weather.py      Open-Meteo weather
    tests/

A new skill is one file in cipher/skills/ using the @skill decorator. Add its
name to a mode's tool list in personality.py to enable it there.

## Tests

    python -m unittest discover tests

The tests run offline.

## Security design

- Active tools refuse any host outside the user-managed scope list
- The Telegram bot ignores every sender except the owner
- Log analysis only reads files inside ~/.cipher/logs/
- Tokens and API keys are scrubbed from logs and replies
- CIPHER does not write malware or exploits

## Responsible use

Only scan and audit systems you own or have written permission to test.
You are responsible for how you use this tool.

## License

MIT, see LICENSE.
