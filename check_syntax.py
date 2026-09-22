with open('dashboard/static/js/dashboard.js', 'rb') as f:
    lines = f.readlines()
for i in range(2240, 2260):
    if i < len(lines):
        print(f'{i+1}: {repr(lines[i].decode("utf-8", errors="replace"))}')
