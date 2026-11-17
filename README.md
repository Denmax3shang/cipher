# CIPHER

A personal cybersecurity AI assistant for Termux. It chats like a normal AI,
remembers facts about you, keeps notes, and runs security tools on your behalf.

## Features

- Natural-language chat with tool calling (any OpenAI-compatible API)
- Persistent memory and notes, stored in ~/.cipher/
- Security skills: hash identifier, hasher, password strength check,
  password generator, DNS lookup, port scanner, HTTP security-header audit,
  SSH/web log analyzer
- Scope guard: scans and audits only run on hosts you add with /scope add
- Optional Telegram front-end, locked to your account

## Install

    pkg install python git -y
    git clone <your-repo-url> cipher_project
    cd cipher_project
    pip install -r requirements.txt

## Configure

    export LLM_API_KEY="your-key"
    export LLM_MODEL="openai/gpt-oss-120b"
    export LLM_BASE_URL="https://api.groq.com/openai/v1"

Any OpenAI-compatible provider works. Keys are read from environment
variables only and are never stored in this repo.

## Run

    python -m cipher

Commands: /help, /scope add|remove|list, /clear, /exit

## Telegram bot

    export TELEGRAM_TOKEN="token-from-botfather"
    export TELEGRAM_OWNER_ID="your-numeric-id"
    python -m cipher.telegram_bot

Messages from any other account are ignored.

## Tests

    python -m unittest discover tests

## Responsible use

Only scan and audit systems you own or have written permission to test.
The scope list exists to enforce that. You are responsible for how you use
this tool.
