#!/usr/bin/env python3
"""
Wires the new FulaniPlaybackController into QuranActivity and PagerActivity.

What this script does:
  1. Adds seven new string resources to app/src/main/res/values/strings.xml.
  2. In QuranActivity.kt and PagerActivity.kt:
       - Adds the import for FulaniPlaybackController.
       - Adds a `private val fulaniPlaybackController by lazy { ... }` field.
       - Replaces the body of playFulaniTrack(...) to delegate to the controller.
       - Replaces stopFulaniAudio()'s body to delegate to the controller.

Idempotent — safe to run multiple times. Run from the project root.

Prerequisite: place FulaniPlaybackController.kt at
  app/src/main/java/com/quran/labs/androidquran/ui/helpers/FulaniPlaybackController.kt
"""
import re
import sys


NEW_STRINGS = [
    ('fulani_now_playing',     'Now playing'),
    ('fulani_play',            '▶ Play'),
    ('fulani_pause',           '⏸ Pause'),
    ('fulani_rewind_10s',      '−10s'),
    ('fulani_forward_10s',     '+10s'),
    ('fulani_loading_short',   'Loading…'),
    ('fulani_playing_short',   'Playing'),
    ('fulani_finished',        'Finished'),
]


def add_strings_xml() -> str:
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


def patch_activity(name: str, path: str, class_name: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  {name}: NOT FOUND at {path}"

    original = content
    changes = []

    # 1. Add the import.
    controller_import = (
        "import com.quran.labs.androidquran.ui.helpers.FulaniPlaybackController"
    )
    if controller_import not in content:
        m = list(re.finditer(r"^import .+$", content, re.MULTILINE))
        if not m:
            return f"  {name}: no imports found — manual edit needed"
        end = m[-1].end()
        content = content[:end] + "\n" + controller_import + content[end:]
        changes.append("import")

    # 2. Add the field declaration.
    # Anchor: insert right before the first `fulaniMediaPlayer` field (which both
    # activities currently have).
    field_decl = (
        "  private val fulaniPlaybackController by lazy { FulaniPlaybackController(this) }"
    )
    if "fulaniPlaybackController" not in content:
        anchor = "private var fulaniMediaPlayer: MediaPlayer? = null"
        if anchor not in content:
            return f"  {name}: field anchor 'fulaniMediaPlayer' not found"
        content = content.replace(anchor, field_decl + "\n  " + anchor, 1)
        changes.append("field")

    # 3. Replace the body of playFulaniTrack(track, surah).
    play_re = re.compile(
        r"(private fun playFulaniTrack\(track: FulaniTrack, surah: Int\)\s*\{)"
        r"(.*?)"
        r"(\n  \})",  # closing brace at 2-space indent ends the method
        re.DOTALL,
    )
    m = play_re.search(content)
    if m and "fulaniPlaybackController.play(" not in m.group(2):
        new_body = (
            "\n    val audioUrl = FULANI_BASE_URL + track.file"
            "\n    val surahName = " + _surah_names_const(name) + ".getOrNull(surah - 1) ?: \"\""
            "\n    val label = getString(R.string.fulani_track_label, surah, surahName, track.nisf)"
            "\n    fulaniPlaybackController.play(audioUrl, label)"
        )
        content = content[:m.start()] + m.group(1) + new_body + m.group(3) + content[m.end():]
        changes.append("playFulaniTrack body")

    # 4. Replace the body of stopFulaniAudio() to delegate to the controller.
    stop_re = re.compile(
        r"(private fun stopFulaniAudio\(\)\s*\{)"
        r"(.*?)"
        r"(\n  \})",
        re.DOTALL,
    )
    m = stop_re.search(content)
    if m and "fulaniPlaybackController.stop()" not in m.group(2):
        new_body = "\n    fulaniPlaybackController.stop()"
        content = content[:m.start()] + m.group(1) + new_body + m.group(3) + content[m.end():]
        changes.append("stopFulaniAudio body")

    # 5. Add release() call in onDestroy if not already there.
    if "fulaniPlaybackController.release()" not in content:
        od_re = re.compile(r"(override fun onDestroy\(\)\s*\{\s*\n)(\s*)", re.MULTILINE)
        m = od_re.search(content)
        if m:
            body_start = m.end()
            super_re = re.compile(r"super\.onDestroy\(\)")
            sm = super_re.search(content, body_start)
            if sm:
                indent = m.group(2)
                insertion = f"{indent}fulaniPlaybackController.release()\n"
                content = content[:body_start] + insertion + content[body_start:]
                changes.append("onDestroy release()")

    if content == original:
        return f"  {name}: already up to date"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"  {name}: " + ", ".join(changes)


def _surah_names_const(activity_name: str) -> str:
    # QuranActivity uses SURAH_NAMES; PagerActivity uses FULANI_SURAH_NAMES.
    if "Pager" in activity_name:
        return "FULANI_SURAH_NAMES"
    return "SURAH_NAMES"


def main() -> int:
    print("Wiring playback controls:\n")
    print(add_strings_xml())
    print(patch_activity(
        "QuranActivity",
        "app/src/main/java/com/quran/labs/androidquran/ui/QuranActivity.kt",
        "QuranActivity",
    ))
    print(patch_activity(
        "PagerActivity",
        "app/src/main/java/com/quran/labs/androidquran/ui/PagerActivity.kt",
        "PagerActivity",
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
