# 7-Eleven Thailand Automation

Scripts and docs for automating orders on [ALL Online (7-Eleven Thailand)](https://www.allonline.7eleven.co.th).

## Setup

1. Copy `.env.sample` to `.env` and fill in your credentials:

```bash
cp .env.sample .env
```

2. Edit `.env` with your details:

| Variable | Description |
|----------|-------------|
| `EMAIL_USER` | Your email address (for IMAP login) |
| `EMAIL_PASSWORD` | Your email password |
| `EMAIL_HOST` | IMAP server hostname |
| `EMAIL_PORT` | IMAP port (993 for SSL) |
| `SEVEN_EMAIL` | 7-Eleven account email |
| `SEVEN_PASSWORD` | 7-Eleven account password (legacy, site uses OTP now) |
| `VISION_MODEL` | Vision model name for grid/phone scripts (default: `gemma-4-26B-A4B-it-uncensored-heretic-Q8_0.gguf`) |

3. Install dependencies:

```bash
uv pip install -r requirements.txt
```

## Usage

### Check emails (e.g. to retrieve OTP codes)

```bash
python3 check_email.py       # latest 5 emails
python3 check_email.py 10    # latest 10 emails
```

### Browser automation

Requires Chrome running with remote debugging. See `CLAUDE.md` for full instructions on:
- Launching Chrome with `--remote-debugging-port=9222`
- 7-Eleven OTP login flow
- Filling address forms with cascading dropdowns
