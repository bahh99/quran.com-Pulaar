#!/usr/bin/env python3
"""
Merges the new "About" entry into the existing "About us" menu item.

What it does:
  1. Removes our separate "About" item from home_menu.xml.
  2. Removes the R.id.tafsir_pular_about case from QuranActivity.kt.
  3. Redirects the existing R.id.about case to open TafsirPularAboutActivity
     instead of AboutUsActivity.

Idempotent. Run from the project root.
"""
import re

# ---------------------------------------------------------------------------
# 1. Remove the standalone menu item.
# ---------------------------------------------------------------------------
menu_path = "app/src/main/res/menu/home_menu.xml"
with open(menu_path, "r", encoding="utf-8") as f:
    menu_xml = f.read()

# Match the entire <item .../> for tafsir_pular_about, including the preceding whitespace.
item_re = re.compile(
    r"\s*<item\s+[^/]*?android:id=\"@\+id/tafsir_pular_about\"[^/]*?/>",
    re.DOTALL,
)
new_menu_xml, removed = item_re.subn("", menu_xml)
if removed:
    with open(menu_path, "w", encoding="utf-8") as f:
        f.write(new_menu_xml)
    print(f"home_menu.xml: removed {removed} 'About' item(s).")
else:
    print("home_menu.xml: 'About' item already absent.")


# ---------------------------------------------------------------------------
# 2. Patch QuranActivity.kt: drop the tafsir_pular_about case, redirect about.
# ---------------------------------------------------------------------------
activity_path = "app/src/main/java/com/quran/labs/androidquran/ui/QuranActivity.kt"
with open(activity_path, "r", encoding="utf-8") as f:
    content = f.read()
original = content

# 2a. Remove the R.id.tafsir_pular_about case block entirely.
case_re = re.compile(
    r"\s*R\.id\.tafsir_pular_about\s*->\s*\{[^}]*\}",
    re.DOTALL,
)
new_content, removed_cases = case_re.subn("", content)
if removed_cases:
    content = new_content
    print(f"QuranActivity.kt: removed {removed_cases} R.id.tafsir_pular_about case(s).")
else:
    print("QuranActivity.kt: no standalone tafsir_pular_about case to remove.")

# 2b. Rewire the existing R.id.about case to use TafsirPularAboutActivity.
old_about = "startActivity(Intent(this, AboutUsActivity::class.java))"
new_about = "startActivity(Intent(this, TafsirPularAboutActivity::class.java))"
if old_about in content:
    content = content.replace(old_about, new_about, 1)
    print("QuranActivity.kt: rewired R.id.about to TafsirPularAboutActivity.")
elif new_about in content:
    print("QuranActivity.kt: R.id.about already points at TafsirPularAboutActivity.")
else:
    print("QuranActivity.kt: couldn't find the AboutUsActivity intent line — "
          "manual edit may be needed.")

if content != original:
    with open(activity_path, "w", encoding="utf-8") as f:
        f.write(content)
