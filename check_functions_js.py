import subprocess
import os
import re

with open(r'dashboard/static/js/dashboard.js', 'r', encoding='utf-8') as f:
    code = f.read()

temp_wsf = "temp_check.wsf"

def test_code(code_str):
    wsf_content = '''<job>
<script language="JScript">
try {
    var testFn = new Function(''' + repr(code_str) + ''');
    WScript.Echo("OK");
} catch(e) {
    WScript.Echo("ERR: " + e.message + " at " + e.description);
}
</script>
</job>'''
    with open(temp_wsf, 'w', encoding='utf-8') as f:
        f.write(wsf_content)
    res = subprocess.run(['cscript', '//Nologo', temp_wsf], capture_output=True, text=True)
    if os.path.exists(temp_wsf):
        os.remove(temp_wsf)
    return "OK" in res.stdout, res.stdout.strip()

# Split code into top level blocks or functions
# Or parse line ranges
lines = code.splitlines()

print(f"Total lines: {len(lines)}")

# Test 100-line blocks wrapped in dummy try { ... }
for start in range(0, len(lines), 100):
    end = min(start + 100, len(lines))
    block = "\n".join(lines[start:end])
    # wrap in try/catch or function if possible, but let's test syntax of statements
    # Actually, JS statements can be evaluated inside a function body:
    # "function test() {\n" + block + "\n}"
    wrapped = "function _test_block() {\n" + block + "\n}"
    ok, msg = test_code(wrapped)
    if not ok:
        print(f"Block lines {start+1} to {end} HAS SYNTAX ERROR: {msg}")
        # Now test line by line in this block
        for l_idx in range(start, end):
            sub_block = "\n".join(lines[start:l_idx+1])
            # see if l_idx line causes syntax error when added
            # Let's print the lines in this block to inspect
            pass
