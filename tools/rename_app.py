#!/usr/bin/env python3
"""
Renames the app's launcher label to "Tafsir Pular".

Only updates the base values/strings.xml — localized variants
(values-fr/, values-ar/, etc.) keep their existing translations.
If a locale doesn't define app_name, Android falls back to the base value.

Idempotent. Run from the project root.
"""
import re

PATH = "app/src/main/res/values/strings.xml"
NEW_NAME = "Tafsir Pular"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

original = content
m = re.search(r'<string name="app_name">([^<]*)</string>', content)
if not m:
    print(f"ERROR: <string name=\"app_name\"> not found in {PATH}.")
elif m.group(1) == NEW_NAME:
    print(f"strings.xml: app_name already '{NEW_NAME}'.")
else:
    old = m.group(1)
    content = content.replace(m.group(0), f'<string name="app_name">{NEW_NAME}</string>', 1)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"strings.xml: app_name '{old}' → '{NEW_NAME}'.")
