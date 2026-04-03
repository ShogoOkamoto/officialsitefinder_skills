"""Entry point for python -m extract_address_tool."""
import sys
import io
import json
from extract_address_tool.extract import extract_addresses

if sys.platform == 'win32':
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

if len(sys.argv) > 1:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text_content = f.read()
else:
    text_content = sys.stdin.read()

print(extract_addresses(text_content))
