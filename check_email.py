import imaplib
import email
import os
from email.header import decode_header
from pathlib import Path
import sys

def load_env():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip())

load_env()

def check_emails(num_emails=5):
    host = os.environ['EMAIL_HOST']
    port = int(os.environ['EMAIL_PORT'])
    user = os.environ['EMAIL_USER']
    password = os.environ['EMAIL_PASSWORD']

    mail = imaplib.IMAP4_SSL(host, port)
    try:
        mail.login(user, password)
        mail.select('INBOX')

        status, messages = mail.search(None, 'ALL')
        msg_ids = messages[0].split()

        # Get latest N emails
        latest = msg_ids[-num_emails:] if len(msg_ids) >= num_emails else msg_ids
        latest.reverse()  # newest first

        for mid in latest:
            status, msg_data = mail.fetch(mid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # Decode subject
            subject_parts = decode_header(msg['Subject'] or '')
            subject = ''
            for part, enc in subject_parts:
                if isinstance(part, bytes):
                    subject += part.decode(enc or 'utf-8', errors='replace')
                else:
                    subject += part

            print(f"--- Email ID: {mid.decode()} ---")
            print(f"From: {msg['From']}")
            print(f"Date: {msg['Date']}")
            print(f"Subject: {subject}")

            # Get body
            if msg.is_multipart():
                for part in msg.walk():
                    ct = part.get_content_type()
                    if ct == 'text/plain':
                        body = part.get_payload(decode=True).decode(errors='replace')
                        print(f"Body:\n{body[:500]}")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='replace')
                print(f"Body:\n{body[:500]}")
            print()
    finally:
        mail.logout()

if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    check_emails(n)
