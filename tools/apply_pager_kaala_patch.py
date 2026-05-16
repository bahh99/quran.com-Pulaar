#!/usr/bin/env python3
"""
Applies the Sheikh Kaala / Fulani audio play-button interception patch to
PagerActivity.kt. Idempotent — safe to run multiple times.

Usage (from the quran_android project root):
    python3 apply_pager_kaala_patch.py
"""
import re
import sys

PATH = "app/src/main/java/com/quran/labs/androidquran/ui/PagerActivity.kt"


def main() -> int:
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERROR: {PATH} not found. Run this from the project root.")
        return 1

    original = content
    changes = []

    # ---- 1. Add imports ----
    required_imports = [
        "import android.media.MediaPlayer",
        "import kotlinx.coroutines.Dispatchers",
        "import kotlinx.coroutines.withContext",
        "import org.json.JSONObject",
        "import java.net.URL",
    ]
    for imp in required_imports:
        if imp in content:
            continue
        # Insert after the last existing import line.
        m = list(re.finditer(r"^import .+$", content, re.MULTILINE))
        if not m:
            print("ERROR: no imports found in file.")
            return 1
        end = m[-1].end()
        content = content[:end] + "\n" + imp + content[end:]
        changes.append(f"added import: {imp}")

    # ---- 2. Add Fulani state fields right after the qariManager injection ----
    field_anchor = "@Inject lateinit var qariManager: CurrentQariManager"
    fields_block = (
        "\n"
        "\n  // Sheikh Kaala / Fulani audio state (separate from the standard audio service)"
        "\n  private var fulaniMediaPlayer: MediaPlayer? = null"
        "\n  private var fulaniIndexCache: List<FulaniTrack>? = null"
    )
    if "fulaniMediaPlayer" not in content:
        if field_anchor not in content:
            print("ERROR: field anchor not found (expected 'qariManager: CurrentQariManager').")
            return 1
        content = content.replace(field_anchor, field_anchor + fields_block, 1)
        changes.append("added fulaniMediaPlayer / fulaniIndexCache fields")

    # ---- 3. Insert Kaala interception at the top of onPlayPressed() ----
    if "FULANI_KAALA_QARI_ID" not in content:
        # Match: override fun onPlayPressed() {  (and capture the indentation of the next line)
        op_re = re.compile(
            r"(override fun onPlayPressed\(\)\s*\{\s*\n)(\s*)",
            re.MULTILINE,
        )
        m = op_re.search(content)
        if not m:
            print("ERROR: onPlayPressed() declaration not found.")
            return 1
        indent = m.group(2)
        interception = (
            f"{indent}// Sheikh Kaala uses chunk-based audio; route to the Fulani nisf picker.\n"
            f"{indent}if (qariManager.currentQari().id == FULANI_KAALA_QARI_ID) {{\n"
            f"{indent}  val position = viewPager.currentItem\n"
            f"{indent}  val page = quranInfo.getPageFromPosition(position, isDualPageVisible)\n"
            f"{indent}  val startSura = quranDisplayData.safelyGetSuraOnPage(page)\n"
            f"{indent}  showFulaniNisfPickerForSurah(startSura)\n"
            f"{indent}  return\n"
            f"{indent}}}\n"
            f"{indent}\n"
        )
        content = content[: m.end()] + interception + content[m.end():]
        changes.append("inserted Kaala check at top of onPlayPressed()")

    # ---- 4. Append helper methods + Fulani data class before the companion object ----
    if "private fun showFulaniNisfPickerForSurah" not in content:
        helpers = '''
  // region Sheikh Kaala / Fulani audio (chunk-based playback)

  private data class FulaniTrack(
    val file: String,
    val nisf: Int,
    val startSurah: Int,
    val startVerse: Int,
    val endSurah: Int,
    val endVerse: Int
  )

  private suspend fun loadFulaniIndex(): List<FulaniTrack> {
    fulaniIndexCache?.let { return it }
    return withContext(Dispatchers.IO) {
      val url = URL(FULANI_INDEX_URL)
      val text = url.readText()
      val json = JSONObject(text)
      val files = json.getJSONArray("files")
      val list = ArrayList<FulaniTrack>(files.length())
      for (i in 0 until files.length()) {
        val obj = files.getJSONObject(i)
        list.add(
          FulaniTrack(
            file = obj.getString("file"),
            nisf = obj.optInt("nisf", 0),
            startSurah = obj.getInt("startSurah"),
            startVerse = obj.getInt("startVerse"),
            endSurah = obj.getInt("endSurah"),
            endVerse = obj.getInt("endVerse")
          )
        )
      }
      fulaniIndexCache = list
      list
    }
  }

  private fun showFulaniNisfPickerForSurah(surah: Int) {
    lifecycleScope.launch {
      try {
        val tracks = loadFulaniIndex().filter {
          it.startSurah <= surah && surah <= it.endSurah
        }
        if (tracks.isEmpty()) {
          Toast.makeText(
            this@PagerActivity,
            getString(R.string.fulani_surah_not_covered, surah),
            Toast.LENGTH_LONG
          ).show()
          return@launch
        }
        val surahName = FULANI_SURAH_NAMES.getOrNull(surah - 1) ?: ""
        val labels = tracks.map { track ->
          val coverage = when {
            track.startSurah == surah && track.endSurah == surah ->
              getString(R.string.fulani_verses_range, track.startVerse, track.endVerse)
            track.startSurah == surah ->
              getString(R.string.fulani_verses_from, track.startVerse)
            track.endSurah == surah ->
              getString(R.string.fulani_verses_until, track.endVerse)
            else ->
              getString(R.string.fulani_verses_full)
          }
          getString(R.string.fulani_nisf_entry, track.nisf, coverage)
        }.toTypedArray()
        AlertDialog.Builder(this@PagerActivity)
          .setTitle(getString(R.string.fulani_pick_nisf, surah, surahName))
          .setItems(labels) { _, which -> playFulaniTrack(tracks[which], surah) }
          .setNegativeButton(android.R.string.cancel, null)
          .setNeutralButton(R.string.fulani_stop) { _, _ -> stopFulaniAudio() }
          .show()
      } catch (e: Exception) {
        Toast.makeText(
          this@PagerActivity,
          getString(R.string.fulani_load_error, e.message ?: ""),
          Toast.LENGTH_LONG
        ).show()
      }
    }
  }

  private fun playFulaniTrack(track: FulaniTrack, surah: Int) {
    stopFulaniAudio()
    val audioUrl = FULANI_BASE_URL + track.file
    val surahName = FULANI_SURAH_NAMES.getOrNull(surah - 1) ?: ""
    val label = getString(R.string.fulani_track_label, surah, surahName, track.nisf)
    Toast.makeText(
      this,
      getString(R.string.fulani_loading, label),
      Toast.LENGTH_SHORT
    ).show()
    fulaniMediaPlayer = MediaPlayer().apply {
      try {
        setDataSource(audioUrl)
      } catch (e: Exception) {
        Toast.makeText(
          this@PagerActivity,
          getString(R.string.fulani_load_error, e.message ?: ""),
          Toast.LENGTH_LONG
        ).show()
        release()
        fulaniMediaPlayer = null
        return
      }
      setOnPreparedListener {
        it.start()
        Toast.makeText(
          this@PagerActivity,
          getString(R.string.fulani_playing, label),
          Toast.LENGTH_SHORT
        ).show()
      }
      setOnCompletionListener { stopFulaniAudio() }
      setOnErrorListener { _, what, extra ->
        Toast.makeText(
          this@PagerActivity,
          getString(R.string.fulani_playback_error, what, extra),
          Toast.LENGTH_LONG
        ).show()
        stopFulaniAudio()
        true
      }
      prepareAsync()
    }
  }

  private fun stopFulaniAudio() {
    fulaniMediaPlayer?.let { mp ->
      try {
        if (mp.isPlaying) mp.stop()
      } catch (_: IllegalStateException) {
        // already in invalid state
      }
      mp.release()
    }
    fulaniMediaPlayer = null
  }

  // endregion
'''
        # Insert immediately before the companion object.
        co_re = re.compile(r"\n(\s*)companion object\s*\{", re.MULTILINE)
        m = co_re.search(content)
        if not m:
            print("ERROR: companion object not found.")
            return 1
        insert_pos = m.start()
        content = content[:insert_pos] + helpers + content[insert_pos:]
        changes.append("inserted Fulani helper methods")

    # ---- 5. Add stopFulaniAudio() call inside onDestroy() ----
    if "stopFulaniAudio()" not in content.split("companion object")[0].split("override fun onDestroy")[-1] or content.count("stopFulaniAudio()") < 2:
        # We need stopFulaniAudio() to appear inside onDestroy. The helpers
        # block already references stopFulaniAudio elsewhere; check the count.
        # The helpers block contains 3 references. So total should be >= 4 once
        # we add the onDestroy call. Re-check by looking inside onDestroy.
        od_re = re.compile(r"(override fun onDestroy\(\)\s*\{\s*\n)(\s*)", re.MULTILINE)
        m = od_re.search(content)
        if not m:
            print("WARNING: onDestroy() not found — stopFulaniAudio() not wired into onDestroy. "
                  "The MediaPlayer will be released when the activity is GC'd, but you should "
                  "add `stopFulaniAudio()` to onDestroy manually for cleanliness.")
        else:
            # Only add if not already there in the onDestroy body
            body_start = m.end()
            # Find end of onDestroy body — approximate by searching for the matching brace.
            # Simple heuristic: look for first `super.onDestroy()` after the match.
            super_call_re = re.compile(r"super\.onDestroy\(\)")
            sm = super_call_re.search(content, body_start)
            if sm:
                onDestroy_body = content[body_start:sm.start()]
                if "stopFulaniAudio()" not in onDestroy_body:
                    indent = m.group(2)
                    insertion = f"{indent}stopFulaniAudio()\n"
                    content = content[:body_start] + insertion + content[body_start:]
                    changes.append("added stopFulaniAudio() call to onDestroy()")

    # ---- 6. Add constants & SURAH_NAMES to the companion object ----
    if "FULANI_KAALA_QARI_ID = 3" not in content:
        constants_block = '''
    private const val FULANI_KAALA_QARI_ID = 3
    private const val FULANI_BASE_URL =
      "https://pub-3059b47aefff4962baaf555118627f70.r2.dev/"
    private const val FULANI_INDEX_URL =
      FULANI_BASE_URL + "fulani-audio-index.json"

    /** Surah names (mushaf order, index 0..113 for surahs 1..114). */
    private val FULANI_SURAH_NAMES = listOf(
      "Al-Fātihah", "Al-Baqarah", "Āli ʿImrān", "An-Nisāʾ", "Al-Māʾidah",
      "Al-Anʿām", "Al-Aʿrāf", "Al-Anfāl", "At-Tawbah", "Yūnus",
      "Hūd", "Yūsuf", "Ar-Raʿd", "Ibrāhīm", "Al-Hijr",
      "An-Nahl", "Al-Isrāʾ", "Al-Kahf", "Maryam", "Tāhā",
      "Al-Anbiyāʾ", "Al-Hajj", "Al-Muʾminūn", "An-Nūr", "Al-Furqān",
      "Ash-Shuʿarāʾ", "An-Naml", "Al-Qasas", "Al-ʿAnkabūt", "Ar-Rūm",
      "Luqmān", "As-Sajdah", "Al-Ahzāb", "Sabaʾ", "Fātir",
      "Yāsīn", "As-Sāffāt", "Sād", "Az-Zumar", "Ghāfir",
      "Fussilat", "Ash-Shūrā", "Az-Zukhruf", "Ad-Dukhān", "Al-Jāthiyah",
      "Al-Ahqāf", "Muhammad", "Al-Fath", "Al-Hujurāt", "Qāf",
      "Adh-Dhāriyāt", "At-Tūr", "An-Najm", "Al-Qamar", "Ar-Rahmān",
      "Al-Wāqiʿah", "Al-Hadīd", "Al-Mujādilah", "Al-Hashr", "Al-Mumtahanah",
      "As-Saff", "Al-Jumuʿah", "Al-Munāfiqūn", "At-Taghābun", "At-Talāq",
      "At-Tahrīm", "Al-Mulk", "Al-Qalam", "Al-Hāqqah", "Al-Maʿārij",
      "Nūh", "Al-Jinn", "Al-Muzzammil", "Al-Muddaththir", "Al-Qiyāmah",
      "Al-Insān", "Al-Mursalāt", "An-Nabaʾ", "An-Nāziʿāt", "ʿAbasa",
      "At-Takwīr", "Al-Infitār", "Al-Mutaffifīn", "Al-Inshiqāq", "Al-Burūj",
      "At-Tāriq", "Al-Aʿlā", "Al-Ghāshiyah", "Al-Fajr", "Al-Balad",
      "Ash-Shams", "Al-Layl", "Ad-Duhā", "Ash-Sharh", "At-Tīn",
      "Al-ʿAlaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-ʿĀdiyāt",
      "Al-Qāriʿah", "At-Takāthur", "Al-ʿAsr", "Al-Humazah", "Al-Fīl",
      "Quraysh", "Al-Māʿūn", "Al-Kawthar", "Al-Kāfirūn", "An-Nasr",
      "Al-Masad", "Al-Ikhlās", "Al-Falaq", "An-Nās"
    )
'''
        # Insert just after the opening brace of the companion object.
        co_re = re.compile(r"(companion object\s*\{\s*\n)", re.MULTILINE)
        m = co_re.search(content)
        if not m:
            print("ERROR: companion object opening not found.")
            return 1
        content = content[: m.end()] + constants_block + content[m.end():]
        changes.append("added FULANI_* constants and SURAH_NAMES to companion object")

    if content == original:
        print("No changes applied — file already patched.")
        return 0

    with open(PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Patched {PATH}:")
    for c in changes:
        print(f"  - {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
