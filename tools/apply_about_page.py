#!/usr/bin/env python3
"""
Wires up the TafsirPularAboutActivity:

  1. Adds 7 string resources to app/src/main/res/values/strings.xml.
  2. Adds a menu entry to app/src/main/res/menu/home_menu.xml.
  3. Registers the activity in app/src/main/AndroidManifest.xml.
  4. Adds a click handler in QuranActivity.kt.

Prerequisite: copy TafsirPularAboutActivity.kt to
  app/src/main/java/com/quran/labs/androidquran/ui/TafsirPularAboutActivity.kt

Idempotent. Run from the project root.
"""
import re
import sys


NEW_STRINGS = [
    ("tafsir_pular_about_menu",          "About"),
    ("tafsir_pular_about_title",         "About"),
    ("tafsir_pular_about_intro",
     "Tafsir Pular is a Qur\\'an reader app featuring complete recitation "
     "and tafsir in the Fulani (Pular) language."),
    ("tafsir_pular_about_reciter_heading", "Recitation &amp; Tafsir"),
    ("tafsir_pular_about_reciter_body",
     "All Fulani audio in this app is the recitation and tafsir of "
     "Sheikh Abdullah Kaala. May Allah reward him for his work in making "
     "the Qur\\'an accessible to Fulani-speakers worldwide."),
    ("tafsir_pular_about_quran_heading",  "Built on Quran for Android"),
    ("tafsir_pular_about_quran_body",
     "This app is built upon the open-source &lt;b&gt;Quran for Android&lt;/b&gt; "
     "project, developed by the Quran.com team and the broader open-source "
     "community. The Fulani audio integration has been added on top of that "
     "foundation.&lt;br/&gt;&lt;br/&gt;"
     "Project: &lt;a href=\"https://github.com/quran/quran_android\"&gt;"
     "github.com/quran/quran_android&lt;/a&gt;"),
    ("tafsir_pular_about_license",
     "Licensed under the GNU General Public License v3.0 (GPL-3.0)."),
]


def add_strings() -> str:
    path = "app/src/main/res/values/strings.xml"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  strings.xml: NOT FOUND at {path}"

    added = []
    for key, value in NEW_STRINGS:
        if f'name="{key}"' in content:
            continue
        new_line = f'  <string name="{key}">{value}</string>'
        content = content.replace("</resources>", new_line + "\n</resources>", 1)
        added.append(key)

    if not added:
        return "  strings.xml: already up to date"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"  strings.xml: added " + ", ".join(added)


def add_menu_item() -> str:
    path = "app/src/main/res/menu/home_menu.xml"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  home_menu.xml: NOT FOUND at {path}"

    if "tafsir_pular_about" in content:
        return "  home_menu.xml: menu item already present"

    new_item = (
        '\n    <item\n'
        '        android:id="@+id/tafsir_pular_about"\n'
        '        android:title="@string/tafsir_pular_about_menu"\n'
        '        app:showAsAction="never" />\n'
    )

    # Insert before the closing </menu> tag.
    if "</menu>" not in content:
        return "  home_menu.xml: no </menu> close tag found — manual edit needed"
    content = content.replace("</menu>", new_item + "</menu>", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "  home_menu.xml: added tafsir_pular_about menu item"


def add_manifest_entry() -> str:
    path = "app/src/main/AndroidManifest.xml"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  AndroidManifest.xml: NOT FOUND at {path}"

    if "TafsirPularAboutActivity" in content:
        return "  AndroidManifest.xml: activity already registered"

    new_entry = (
        '\n    <activity\n'
        '        android:name=".ui.TafsirPularAboutActivity"\n'
        '        android:parentActivityName=".ui.QuranActivity"\n'
        '        android:label="@string/tafsir_pular_about_title"\n'
        '        android:exported="false" />\n'
    )

    # Find an anchor: the existing QuranActivity declaration (which we know exists).
    anchor_re = re.compile(
        r'(<activity[^>]*android:name=["\']\.ui\.QuranActivity["\'][^/>]*(?:/>|>.*?</activity>))',
        re.DOTALL,
    )
    m = anchor_re.search(content)
    if not m:
        return "  AndroidManifest.xml: QuranActivity anchor not found — manual edit needed"
    insert_pos = m.end()
    content = content[:insert_pos] + new_entry + content[insert_pos:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "  AndroidManifest.xml: registered TafsirPularAboutActivity"


def add_click_handler() -> str:
    path = "app/src/main/java/com/quran/labs/androidquran/ui/QuranActivity.kt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  QuranActivity.kt: NOT FOUND at {path}"

    if "R.id.tafsir_pular_about" in content:
        return "  QuranActivity.kt: click handler already present"

    # Insert a new when-branch right before the fulani_audio branch (a stable
    # anchor that we know exists in the user's version).
    anchor = "R.id.fulani_audio -> {"
    if anchor not in content:
        return "  QuranActivity.kt: R.id.fulani_audio anchor not found — manual edit needed"

    new_branch = (
        "R.id.tafsir_pular_about -> {\n"
        "        startActivity(Intent(this, TafsirPularAboutActivity::class.java))\n"
        "      }\n"
        "      R.id.fulani_audio -> {"
    )
    content = content.replace(anchor, new_branch, 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "  QuranActivity.kt: added R.id.tafsir_pular_about click handler"


def main() -> int:
    print("Wiring up the About page:\n")
    print(add_strings())
    print(add_menu_item())
    print(add_manifest_entry())
    print(add_click_handler())
    return 0


if __name__ == "__main__":
    sys.exit(main())
