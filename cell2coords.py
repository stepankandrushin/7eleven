import sys

GRID = 64

cell = sys.argv[1].strip()
col_str = ""
row_str = ""
for ch in cell:
    if ch.isalpha():
        col_str += ch.upper()
    elif ch.isdigit():
        row_str += ch

col = 0
for ch in col_str:
    col = col * 26 + (ord(ch) - ord('A') + 1)
col -= 1

row = int(row_str) - 1

x = col * GRID + GRID // 2
y = row * GRID + GRID // 2

print(f"({x}, {y})")
