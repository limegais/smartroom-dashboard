import os

JS_FILE = os.path.join(os.path.dirname(__file__), 'static', 'js', 'dashboard.js')

with open(JS_FILE, 'r', encoding='utf-8') as f:
    src = f.read()

# Replace literal backslash-n (\\n) with newline character escape for JS (\n)
new_src = src.replace('\\\\n', '\\n')

with open(JS_FILE, 'w', encoding='utf-8') as f:
    f.write(new_src)

print("Replaced \\\\n with \\n successfully.")
