#!/usr/bin/env python3
"""
Applies the two still-missing Sheikh Kaala changes:

  1. Adds the 4th Qari (id=3) to MadaniPageProvider.getQaris().
  2. Adds the CurrentQariManager observer + injection to QuranActivity.kt.

Idempotent — safe to run multiple times. Run from the project root.
"""
import re
import sys


def fix_madani_page_provider() -> str:
    path = "pages/madani/src/main/java/com/quran/data/page/provider/madani/MadaniPageProvider.kt"

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  MadaniPageProvider: NOT FOUND at {path}"

    if "qari_kaala_tafsir_pular" in content:
        return "  MadaniPageProvider: already present"

    pattern = re.compile(
        r"(audioR\.string\.qari_basfar.*?db\s*=\s*null\s*\n\s*\))(\s*\n)(\s*)\)",
        re.DOTALL,
    )
    m = pattern.search(content)
    if not m:
        return ("  MadaniPageProvider: couldn't find the Basfar entry. "
                "Manual edit needed.")

    basfar_block = m.group(1)
    sep = m.group(2)
    listOf_indent = m.group(3)
    new_qari = (
        '      Qari(\n'
        '        3,\n'
        '        audioR.string.qari_kaala_tafsir_pular,\n'
        '        url = "https://pub-3059b47aefff4962baaf555118627f70.r2.dev/",\n'
        '        path = "kaala_pular",\n'
        '        hasGaplessAlternative = false,\n'
        '        db = "kaala_pular"\n'
        '      )'
    )
    replacement = basfar_block + ",\n" + new_qari + sep + listOf_indent + ")"
    content = content[: m.start()] + replacement + content[m.end():]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "  MadaniPageProvider: added Sheikh Kaala as Qari id=3"


def fix_quran_activity() -> str:
    path = "app/src/main/java/com/quran/labs/androidquran/ui/QuranActivity.kt"

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return f"  QuranActivity: NOT FOUND at {path}"

    original = content
    changes = []

    # 1. Add the CurrentQariManager import (if missing).
    cqm_import = "import com.quran.labs.androidquran.common.audio.repository.CurrentQariManager"
    if cqm_import not in content:
        # Insert after the last existing import line in alphabetical-ish order.
        anchor = "import com.quran.labs.androidquran.SearchActivity"
        if anchor in content:
            content = content.replace(anchor, anchor + "\n" + cqm_import, 1)
            changes.append("CurrentQariManager import")
        else:
            # Fallback: insert after the last import line.
            m = list(re.finditer(r"^import .+$", content, re.MULTILINE))
            if not m:
                return "  QuranActivity: no imports found — manual edit needed"
            end = m[-1].end()
            content = content[:end] + "\n" + cqm_import + content[end:]
            changes.append("CurrentQariManager import (appended)")

    # 2. Add kotlinx.coroutines.flow.drop and distinctUntilChanged (if missing).
    for imp in [
        "import kotlinx.coroutines.flow.distinctUntilChanged",
        "import kotlinx.coroutines.flow.drop",
    ]:
        if imp not in content:
            # Insert near other kotlinx.coroutines imports.
            anchor = "import kotlinx.coroutines.Dispatchers"
            if anchor in content:
                content = content.replace(anchor, anchor + "\n" + imp, 1)
            else:
                m = list(re.finditer(r"^import .+$", content, re.MULTILINE))
                if not m:
                    return "  QuranActivity: no imports found — manual edit needed"
                end = m[-1].end()
                content = content[:end] + "\n" + imp + content[end:]
            short = imp.rsplit(".", 1)[-1]
            changes.append(f"{short} import")

    # 3. Add @Inject lateinit var currentQariManager (if missing).
    if "currentQariManager: CurrentQariManager" not in content:
        # Insert after the existing extraScreens injection (a stable anchor we know exists).
        anchor_re = re.compile(
            r"(@Inject\s*\n\s*lateinit var extraScreens:[^\n]*\n)",
            re.MULTILINE,
        )
        m = anchor_re.search(content)
        if not m:
            return "  QuranActivity: extraScreens injection anchor not found — manual edit needed"
        injection_block = (
            "  @Inject\n"
            "  lateinit var currentQariManager: CurrentQariManager\n"
        )
        content = content[: m.end()] + injection_block + content[m.end():]
        changes.append("currentQariManager @Inject field")

    # 4. Add observeKaalaQariSelection() function (if missing).
    if "observeKaalaQariSelection" not in content:
        observer_block = '''

  /**
   * Observes the current-qari flow. When the user picks Sheikh Kaala from the
   * standard qari list, this opens the surah/nisf picker — the same one the
   * three-dot menu item uses. drop(1) skips the initial saved value so we don't
   * pop the dialog on app launch when Kaala happens to already be selected.
   */
  private fun observeKaalaQariSelection() {
    lifecycleScope.launch {
      currentQariManager.flow()
        .distinctUntilChanged { a, b -> a.id == b.id }
        .drop(1)
        .collect { qari ->
          if (qari.id == FULANI_KAALA_QARI_ID) {
            showFulaniSurahPicker()
          }
        }
    }
  }'''
        # Insert immediately before the FulaniTrack data class.
        anchor_re = re.compile(r"(\n\s*/\*\*\s*\n\s*\*\s*Data class describing a single Fulani audio track)", re.MULTILINE)
        m = anchor_re.search(content)
        if m:
            content = content[: m.start()] + observer_block + content[m.start():]
            changes.append("observeKaalaQariSelection() method")
        else:
            return "  QuranActivity: FulaniTrack anchor not found — manual edit needed"

    # 5. Call observeKaalaQariSelection() in onCreate (if not already called).
    if "observeKaalaQariSelection()" not in content or content.count("observeKaalaQariSelection()") < 2:
        # The function definition counts as 1 occurrence. We need a 2nd (the call).
        anchor = "quranIndexEventLogger.logAnalytics()"
        if anchor in content:
            content = content.replace(
                anchor,
                anchor + "\n    observeKaalaQariSelection()",
                1,
            )
            changes.append("observeKaalaQariSelection() call in onCreate")
        else:
            return "  QuranActivity: onCreate anchor not found — manual edit needed"

    # 6. Add FULANI_KAALA_QARI_ID constant to the companion object (if missing).
    if "FULANI_KAALA_QARI_ID" not in content:
        # Insert right after FULANI_INDEX_URL definition.
        anchor_re = re.compile(
            r'(private const val FULANI_INDEX_URL\s*=\s*\n?\s*FULANI_BASE_URL\s*\+\s*"fulani-audio-index\.json")',
            re.MULTILINE,
        )
        m = anchor_re.search(content)
        if not m:
            return "  QuranActivity: FULANI_INDEX_URL anchor not found — manual edit needed"
        constant_block = (
            "\n\n    /**\n"
            "     * Qari ID for Sheikh Abdullah Kaala in MadaniPageProvider.getQaris().\n"
            "     * Keep this in sync with the entry in pages/madani/.../MadaniPageProvider.kt.\n"
            "     */\n"
            "    private const val FULANI_KAALA_QARI_ID = 3"
        )
        content = content[: m.end()] + constant_block + content[m.end():]
        changes.append("FULANI_KAALA_QARI_ID constant")

    if content == original:
        return "  QuranActivity: already fully patched"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return "  QuranActivity: " + ", ".join(changes)


def main() -> int:
    print("Applying remaining Sheikh Kaala changes:\n")
    print(fix_madani_page_provider())
    print(fix_quran_activity())
    return 0


if __name__ == "__main__":
    sys.exit(main())
