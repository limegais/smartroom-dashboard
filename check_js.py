import sys

with open(r'dashboard\static\js\dashboard.js', 'r', encoding='utf-8') as f:
    c = f.read()

p, b, s = 0, 0, 0
in_str = False
str_char = ''
in_line_comment = False
in_block_comment = False
escaped = False

lines = []
line_num = 1
for i, ch in enumerate(c):
    if ch == '\n':
        lines.append(f"Line {line_num}: p={p}, b={b}, s={s}")
        line_num += 1
        in_line_comment = False
        continue
        
    if in_line_comment:
        continue
        
    if in_block_comment:
        if ch == '*' and i+1 < len(c) and c[i+1] == '/':
            in_block_comment = False
        continue
        
    if in_str:
        if escaped:
            escaped = False
        elif ch == '\\':
            escaped = True
        elif ch == str_char:
            in_str = False
        continue
        
    if ch == '/' and i+1 < len(c):
        if c[i+1] == '/':
            in_line_comment = True
            continue
        elif c[i+1] == '*':
            in_block_comment = True
            continue
            
    if ch in ("'", '"', '`'):
        in_str = True
        str_char = ch
        escaped = False
        continue
        
    if ch == '(': p+=1
    elif ch == ')': p-=1
    elif ch == '{': b+=1
    elif ch == '}': b-=1
    elif ch == '[': s+=1
    elif ch == ']': s-=1

with open('brackets.txt', 'w') as f:
    f.write('\n'.join(lines))
