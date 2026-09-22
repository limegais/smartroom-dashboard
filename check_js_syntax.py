import sys

with open(r'dashboard/static/js/dashboard.js', 'r', encoding='utf-8') as f:
    js_lines = f.readlines()

stack = []
in_block_comment = False

for line_num, line in enumerate(js_lines, 1):
    in_str = False
    str_ch = ''
    escaped = False
    in_line_comment = False
    
    i = 0
    while i < len(line):
        ch = line[i]
        
        if in_block_comment:
            if ch == '*' and i + 1 < len(line) and line[i+1] == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
            
        if in_line_comment:
            break
            
        if in_str:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == str_ch:
                in_str = False
            i += 1
            continue
            
        if ch == '/' and i + 1 < len(line):
            if line[i+1] == '/':
                break
            elif line[i+1] == '*':
                in_block_comment = True
                i += 2
                continue
            
        if ch in ('"', "'", '`'):
            in_str = True
            str_ch = ch
            escaped = False
            i += 1
            continue
            
        if ch in '({[':
            stack.append((ch, line_num, i+1))
        elif ch in ')}]':
            if not stack:
                print(f"Unmatched closing '{ch}' at line {line_num}:{i+1}")
            else:
                top, top_line, top_col = stack.pop()
                expected = {'(': ')', '{': '}', '[': ']'}[top]
                if ch != expected:
                    print(f"Mismatched '{ch}' at line {line_num}:{i+1}, expected '{expected}' for '{top}' from line {top_line}:{top_col}")
        i += 1

print(f"Finished scanning {len(js_lines)} lines. Remaining unclosed in stack: {len(stack)}")
for item in stack[-15:]:
    print("Unclosed:", item)
