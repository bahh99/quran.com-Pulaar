#!/usr/bin/env python3
"""
Adds a "Donate to Mosque" item to the three-dot menu that opens the PayPal
pool URL in the user's browser (after a small confirmation dialog).

  1. Adds 4 string resources to app/src/main/res/values/strings.xml.
  2. Adds a menu entry to app/src/main/res/menu/home_menu.xml.
  3. Adds a click handler with confirmation dialog in QuranActivity.kt.

Idempotent. Run from the project root.
"""
import re
import sys


PAYPAL_URL = "https://www.paypal.com/pools/c/9p9iqugWoJ"

NEW_STRINGS = [
    ("donate_menu",           "Donate to Mosque"),
    ("donate_dialog_title",   "Support the Mosque Project"),
    ("donate_dialog_message",
     "This will open PayPal in your browser to contribute to the mosque "
     "project. May Allah accept your donation."),
    ("donate_dialog_open",    "Open PayPal"),
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

    if 'android:id="@+id/donate"' in content:
        return "  home_menu.xml: donate menu item already present"

    new_item = (
        '\n    <item\n'
        '        android:id="@+id/donate"\n'
        '        android:title="@string/donate_menu"\n'
        '        app:showAsAction="never" />\n'
    )

    if "</menu>" not in content:
        return "  home_menu.xml: no </menu> close tag found — manual edit needed"
    content = content.replace("</menu>", new_item + "</menu>", 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "  home_menu.xml: added donate menu item"


def add_click_handler() -> str:
    path = "app/src/main/java/com/quran/labs/androidquran/ui/QuranActivity.kt"
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  QuranActivity.kt: NOT FOUND at {path}"

    if "R.id.donate" in content:
        return "  QuranActivity.kt: donate handler already present"

    anchor = "R.id.fulani_audio -> {"
    if anchor not in content:
        return "  QuranActivity.kt: anchor not found — manual edit needed"

    new_branch = f'''R.id.donate -> {{
        Builder(this)
          .setTitle(R.string.donate_dialog_title)
          .setMessage(R.string.donate_dialog_message)
          .setPositiveButton(R.string.donate_dialog_open) {{ _, _ ->
            val donateIntent = Intent(Intent.ACTION_VIEW)
            donateIntent.data = "{PAYPAL_URL}".toUri()
            try {{
              startActivity(donateIntent)
            }} catch (_: android.content.ActivityNotFoundException) {{
              // No browser available — silently ignore.
            }}
          }}
          .setNegativeButton(android.R.string.cancel, null)
          .show()
      }}
      R.id.fulani_audio -> {{'''

    content = content.replace(anchor, new_branch, 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "  QuranActivity.kt: added R.id.donate click handler"


def main() -> int:
    print("Wiring up the Donate button:\n")
    print(add_strings())
    print(add_menu_item())
    print(add_click_handler())
    return 0


if __name__ == "__main__":
    sys.exit(main())
