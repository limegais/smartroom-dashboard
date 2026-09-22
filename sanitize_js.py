import re

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Replace common non-ASCII characters
    text = text.replace('°', '\\xB0')
    text = text.replace('—', '-')
    text = text.replace('─', '-')
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    
    # Replace any remaining non-ASCII characters with empty string or space
    cleaned = ''
    for char in text:
        if ord(char) > 127:
            cleaned += ' ' # replace with space to avoid merging tokens
        else:
            cleaned += char
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write(cleaned)

clean_file('dashboard/static/js/dashboard.js')
clean_file('dashboard/static/js/dashboard_v2.js')
