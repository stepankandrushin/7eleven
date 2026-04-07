#!/usr/bin/env python3
"""Take a screenshot of the phone and describe what's on screen, with optional additional prompt."""

import base64
import subprocess
import sys

from openai import OpenAI

# Optional additional prompt from argv
extra_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

# Take screenshot from device
subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
subprocess.run(["adb", "pull", "/sdcard/screen.png", "screen.png"], check=True)

# Encode image (raw screenshot, no grid needed)
with open("screen.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

client = OpenAI(
    base_url="http://localhost:8020/v1",
    api_key="none",
)

system_prompt = (
    "You are a helpful assistant that describes phone screenshots in detail. "
    "Describe the current screen: what app is open, what UI elements are visible, "
    "any text/buttons/icons/popups, the overall layout, and any notable state "
    "(e.g. loading, errors, notifications). Be thorough but organized."
)

user_text = "Describe what's on this phone screen in detail."
if extra_prompt:
    user_text += f"\n\nAlso: {extra_prompt}"

response = client.chat.completions.create(
    # model="gemma-4-31B-it-uncensored-heretic-Q8_0.gguf",
    model="gemma-4-26B-A4B-it-uncensored-heretic-Q8_0.gguf",
    messages=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                },
                {"type": "text", "text": user_text},
            ],
        },
    ],
    temperature=0.1,
    max_tokens=1024,
    extra_body={"chat_template_kwargs": {"enable_thinking": False, "image_token_budget": 1120}},
)

print(response.choices[0].message.content.strip())
