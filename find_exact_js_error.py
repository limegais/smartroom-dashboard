import subprocess
import os

with open(r'dashboard/static/js/dashboard.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# We can test line by line by wrapping lines in a function or testing blocks
temp_wsf = "temp_check.wsf"

def test_code(code_str):
    with open(temp_wsf, 'w', encoding='utf-8') as f:
        f.write('''<job>
<script language="JScript">
try {
    var testFn = new Function(''' + repr(code_str) + ''');
    WScript.Echo("OK");
} catch(e) {
    WScript.Echo("ERR:" + e.message);
}
</script>
</job>''')
    res = subprocess.run(['cscript', '//Nologo', temp_wsf], capture_output=True, text=True)
    if os.path.exists(temp_wsf):
        os.remove(temp_wsf)
    return "OK" in res.stdout

# Check full file first
full_code = "".join(lines)
if test_code(full_code):
    print("Full file is OK!")
else:
    print("Full file has SYNTAX ERROR. Searching for error line...")
    
    # Binary search to find breaking line count
    low = 1
    high = len(lines)
    error_line = high
    
    while low <= high:
        mid = (low + high) // 2
        chunk = "".join(lines[:mid])
        # To make partial chunk valid, we append '}' or closes if needed, but let's test if syntax error is caused by a bad statement
        # Or let's test line by line for illegal characters / syntax
        if not test_code(chunk):
            error_line = mid
            high = mid - 1
        else:
            low = mid + 1
            
    print(f"Syntax error occurs on or before line {error_line}:")
    for l_idx in range(max(0, error_line-5), min(len(lines), error_line+5)):
        print(f"{l_idx+1}: {lines[l_idx].strip()}")
