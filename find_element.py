import base64
import re
import subprocess
import sys

from openai import OpenAI

question = sys.argv[1]

# Take screenshot from device
subprocess.run(["adb", "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
subprocess.run(["adb", "pull", "/sdcard/screen.png", "screen.png"], check=True)

# Generate grid image
subprocess.run(["python3", "grid.py", "screen.png"], check=True)

# Encode image
with open("screen_grid.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

client = OpenAI(
    base_url="http://localhost:8020/v1",
    api_key="none",
)

response = client.chat.completions.create(
    # model="gemma-4-31B-it-uncensored-heretic-Q8_0.gguf",
    model="gemma-4-26B-A4B-it-uncensored-heretic-Q8_0.gguf",
    messages=[
        {
            "role": "system",
            "content": "You are a fast, concise assistant. Respond with only the cell number (like D5). No reasoning required.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_b64}",
                    },
                },
                {
                    "type": "text",
                    "text": f"This is a screenshot with a grid overlay. Columns are labeled with letters at the bottom, rows are numbered on the left. {question}",
                },
            ],
        },
    ],
    temperature=0.1,
    max_tokens=256,
    extra_body={"chat_template_kwargs": {"enable_thinking": False, "image_token_budget": 1120}},
)

cell = response.choices[0].message.content.strip()
print(f"Model response: {cell}")

match = re.search(r'\b([A-Z]{1,2}\d{1,2})\b', cell)
if match:
    cell_ref = match.group(1)
    result = subprocess.run(["python3", "cell2coords.py", cell_ref], capture_output=True, text=True)
    print(f"Cell {cell_ref} -> click at {result.stdout.strip()}")
else:
    print("Could not extract a cell reference from the response.")
