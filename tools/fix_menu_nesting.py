#!/usr/bin/env python3
"""
Fixes the home_menu.xml where tafsir_pular_about and donate items were
inserted into a nested sub-menu by mistake. Moves both to the OUTER menu.

Idempotent. Run from the project root.
"""
import re

PATH = "app/src/main/res/menu/home_menu.xml"

with open(PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Patterns to find our items wherever they currently are.
about_pat = re.compile(
    r"\s*<item\s+android:id=\"@\+id/tafsir_pular_about\""
    r"[^/]*android:title=\"@string/tafsir_pular_about_menu\""
    r"[^/]*app:showAsAction=\"never\"\s*/>",
    re.DOTALL,
)
donate_pat = re.compile(
    r"\s*<item\s+android:id=\"@\+id/donate\""
    r"[^/]*android:title=\"@string/donate_menu\""
    r"[^/]*app:showAsAction=\"never\"\s*/>",
    re.DOTALL,
)

removed_about, n_about = about_pat.subn("", content)
content = removed_about
removed_donate, n_donate = donate_pat.subn("", content)
content = removed_donate

# Locate the OUTERMOST </menu> (the last one in the file).
last_close = content.rfind("</menu>")
if last_close == -1:
    print("ERROR: no </menu> tag found in home_menu.xml — manual edit needed.")
    raise SystemExit(1)

new_items = (
    "\n  <item\n"
    "      android:id=\"@+id/tafsir_pular_about\"\n"
    "      android:title=\"@string/tafsir_pular_about_menu\"\n"
    "      app:showAsAction=\"never\" />\n"
    "  <item\n"
    "      android:id=\"@+id/donate\"\n"
    "      android:title=\"@string/donate_menu\"\n"
    "      app:showAsAction=\"never\" />\n"
)

content = content[:last_close] + new_items + content[last_close:]

with open(PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Removed {n_about} stray about item(s) and {n_donate} stray donate item(s).")
print("Re-inserted both at the top level of the menu (before the outer </menu>).")
