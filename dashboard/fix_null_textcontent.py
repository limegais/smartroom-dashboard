"""
fix_null_textcontent.py
Mengganti semua pola:
    document.getElementById('...').textContent = ...;
menjadi:
    { const _el = document.getElementById('...'); if (_el) _el.textContent = ...; }

sehingga tidak ada lagi crash 'Cannot set properties of null (setting textContent)'.
"""
import re, shutil, os

JS_FILE = os.path.join(os.path.dirname(__file__), 'static', 'js', 'dashboard.js')

# Backup
bak = JS_FILE + '.bak2'
if not os.path.exists(bak):
    shutil.copy2(JS_FILE, bak)
    print(f"Backup: {bak}")

with open(JS_FILE, 'r', encoding='utf-8') as f:
    src = f.read()

# Pattern:
#   document.getElementById('SOME-ID').textContent = EXPR;
# We'll capture the full id string (including possible concatenation like 'brightness-display-' + i)
# and the RHS expression up to the semicolon.
#
# We match:
#   document.getElementById(ID_EXPR).textContent = RHS;
# where ID_EXPR = anything inside (), RHS = everything until ;
#
# We replace with:
#   { var _el = document.getElementById(ID_EXPR); if (_el) _el.textContent = RHS; }

PATTERN = re.compile(
    r"""document\.getElementById\(([^)]+)\)\.textContent\s*=\s*([^;]+);""",
    re.MULTILINE
)

def replacer(m):
    id_expr = m.group(1)
    rhs     = m.group(2).rstrip()
    return f"{{ var _el = document.getElementById({id_expr}); if (_el) _el.textContent = {rhs}; }}"

new_src, count = PATTERN.subn(replacer, src)
print(f"Replaced {count} occurrences")

with open(JS_FILE, 'w', encoding='utf-8') as f:
    f.write(new_src)
print("Done.")
