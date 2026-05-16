#!/usr/bin/env python3
"""
Updates the fulani_play and fulani_pause strings to be just the symbol
(no accompanying word). Idempotent.

Run from the project root.
"""
import re

PATH = "app/src/main/res/values/strings.xml"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

original = content

content = re.sub(
    r'<string name="fulani_play">[^<]*</string>',
    '<string name="fulani_play">▶</string>',
    content,
)
content = re.sub(
    r'<string name="fulani_pause">[^<]*</string>',
    '<string name="fulani_pause">⏸</string>',
    content,
)

if content == original:
    print("strings.xml: no changes needed.")
else:
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("strings.xml: simplified fulani_play / fulani_pause to symbols only.")
