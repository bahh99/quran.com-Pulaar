package com.quran.labs.androidquran.ui.helpers

import android.app.Dialog
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.media.MediaPlayer
import android.text.TextUtils
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.quran.labs.androidquran.R
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Compact, polished playback bar for Sheikh Kaala / Fulani audio.
 *
 * Visual design: floating rounded "card" at the bottom of the screen with
 * a small margin from the edges and a soft drop shadow effect. Auto-hides
 * after [AUTO_HIDE_MS] of no interaction; any tap on the page brings it back.
 */
class FulaniPlaybackController(private val activity: AppCompatActivity) {

  private var mediaPlayer: MediaPlayer? = null
  private var seekBarUpdateJob: Job? = null
  private var autoHideJob: Job? = null
  private var dialog: Dialog? = null
  private var contentView: View? = null

  /** Internal Dialog subclass that converts ACTION_OUTSIDE into an "expand" call. */
  private inner class WatchOutsideDialog(context: Context) : Dialog(context) {
    override fun onTouchEvent(event: MotionEvent): Boolean {
      if (event.action == MotionEvent.ACTION_OUTSIDE) {
        expandBar()
        return true
      }
      return super.onTouchEvent(event)
    }
  }

  /**
   * Builds and shows the playback bar, then begins async preparation of
   * the audio at [audioUrl]. [trackLabel] is shown as the row title.
   */
  fun play(audioUrl: String, trackLabel: String) {
    stop()

    val context: Context = activity
    val density = context.resources.displayMetrics.density
    val padding = (14 * density).toInt()
    val halfPadding = padding / 2
    val cornerRadius = 18 * density
    val edgeMargin = (8 * density).toInt()

    // Outer frame supplies the screen-edge margin via padding; the inner card
    // is what's visually styled (rounded background, content).
    val outerFrame = LinearLayout(context).apply {
      orientation = LinearLayout.VERTICAL
      setPadding(edgeMargin, edgeMargin, edgeMargin, edgeMargin)
    }

    val card = LinearLayout(context).apply {
      orientation = LinearLayout.VERTICAL
      setPadding(padding, padding, padding, padding)
      background = GradientDrawable().apply {
        shape = GradientDrawable.RECTANGLE
        this.cornerRadius = cornerRadius
        setColor(Color.parseColor("#F2202020"))
      }
    }

    // ----- Row 1: track label + time -----
    val labelRow = LinearLayout(context).apply {
      orientation = LinearLayout.HORIZONTAL
      gravity = Gravity.CENTER_VERTICAL
    }
    val labelView = TextView(context).apply {
      text = trackLabel
      textSize = 14f
      maxLines = 1
      setTextColor(Color.WHITE)
      setTypeface(typeface, Typeface.BOLD)
      ellipsize = TextUtils.TruncateAt.END
      layoutParams = LinearLayout.LayoutParams(
        0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f
      )
    }
    labelRow.addView(labelView)

    val timeView = TextView(context).apply {
      text = formatTimeRange(0, 0)
      textSize = 12f
      setTextColor(Color.LTGRAY)
    }
    labelRow.addView(timeView)
    card.addView(labelRow)

    // ----- Row 2: status -----
    val statusView = TextView(context).apply {
      text = context.getString(R.string.fulani_loading_short)
      textSize = 11f
      setTextColor(Color.parseColor("#AAAAAA"))
      setPadding(0, halfPadding / 2, 0, halfPadding)
    }
    card.addView(statusView)

    // ----- Row 3: seek bar -----
    val seekBar = SeekBar(context).apply {
      max = 0
      progress = 0
    }
    card.addView(seekBar)

    // ----- Row 4: circular play/pause button, centred -----
    val buttonsRow = LinearLayout(context).apply {
      orientation = LinearLayout.HORIZONTAL
      gravity = Gravity.CENTER
      setPadding(0, halfPadding, 0, 0)
    }
    val buttonSize = (52 * density).toInt()
    val playPauseButton = Button(context).apply {
      text = context.getString(R.string.fulani_pause)
      textSize = 18f
      setTextColor(Color.WHITE)
      background = GradientDrawable().apply {
        shape = GradientDrawable.OVAL
        setColor(Color.parseColor("#2E7D32"))  // green accent
      }
      includeFontPadding = false
      setPadding(0, 0, 0, 0)
      minWidth = 0
      minimumWidth = 0
      minimumHeight = 0
    }
    val playPauseParams = LinearLayout.LayoutParams(buttonSize, buttonSize)
    buttonsRow.addView(playPauseButton, playPauseParams)
    card.addView(buttonsRow)

    outerFrame.addView(card)
    contentView = outerFrame

    val d = WatchOutsideDialog(context)
    d.setContentView(outerFrame)
    d.setOnDismissListener { stop() }

    d.window?.let { window ->
      window.setFlags(
        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
            WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
            WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH
      )
      window.setDimAmount(0f)
      window.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
      val attrs = window.attributes
      attrs.gravity = Gravity.BOTTOM
      attrs.width = ViewGroup.LayoutParams.MATCH_PARENT
      window.attributes = attrs
    }

    d.show()
    dialog = d

    val mp = MediaPlayer()
    mediaPlayer = mp

    try {
      mp.setDataSource(audioUrl)
    } catch (e: Exception) {
      statusView.text = context.getString(R.string.fulani_load_error, e.message ?: "")
      mp.release()
      mediaPlayer = null
      return
    }

    mp.setOnPreparedListener { ready ->
      ready.start()
      seekBar.max = ready.duration
      statusView.text = context.getString(R.string.fulani_playing_short)
      timeView.text = formatTimeRange(0, ready.duration)
      startSeekBarUpdates(seekBar, timeView)
      scheduleAutoHide()
    }
    mp.setOnCompletionListener {
      seekBarUpdateJob?.cancel()
      autoHideJob?.cancel()
      expandBarNoHide()
      statusView.text = context.getString(R.string.fulani_finished)
      playPauseButton.text = context.getString(R.string.fulani_play)
    }
    mp.setOnErrorListener { _, what, extra ->
      statusView.text = context.getString(R.string.fulani_playback_error, what, extra)
      stop()
      true
    }
    mp.prepareAsync()

    playPauseButton.setOnClickListener {
      val active = mediaPlayer ?: return@setOnClickListener
      try {
        if (active.isPlaying) {
          active.pause()
          playPauseButton.text = context.getString(R.string.fulani_play)
          autoHideJob?.cancel()
        } else {
          active.start()
          playPauseButton.text = context.getString(R.string.fulani_pause)
          startSeekBarUpdates(seekBar, timeView)
          scheduleAutoHide()
        }
      } catch (_: IllegalStateException) {
        // not yet prepared
      }
    }

    seekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
      override fun onProgressChanged(sb: SeekBar?, progress: Int, fromUser: Boolean) {
        if (fromUser) {
          val active = mediaPlayer ?: return
          try {
            active.seekTo(progress)
            timeView.text = formatTimeRange(progress, active.duration)
          } catch (_: IllegalStateException) {
            // not yet prepared
          }
        }
      }
      override fun onStartTrackingTouch(sb: SeekBar?) { autoHideJob?.cancel() }
      override fun onStopTrackingTouch(sb: SeekBar?) { scheduleAutoHide() }
    })
  }

  // ---- Auto-hide state machine ----

  private fun expandBar() {
    val d = dialog ?: return
    val window = d.window ?: return
    val view = contentView ?: return
    val attrs = window.attributes
    attrs.height = ViewGroup.LayoutParams.WRAP_CONTENT
    window.attributes = attrs
    // Fade in
    view.alpha = 0f
    view.animate().alpha(1f).setDuration(180).start()
    scheduleAutoHide()
  }

  /** Expand without restarting the auto-hide timer (used on completion). */
  private fun expandBarNoHide() {
    val d = dialog ?: return
    val window = d.window ?: return
    val view = contentView ?: return
    val attrs = window.attributes
    attrs.height = ViewGroup.LayoutParams.WRAP_CONTENT
    window.attributes = attrs
    view.alpha = 0f
    view.animate().alpha(1f).setDuration(180).start()
    autoHideJob?.cancel()
  }

  private fun collapseBar() {
    val d = dialog ?: return
    val window = d.window ?: return
    val view = contentView ?: return
    // Fade out, then shrink the window once the animation completes.
    view.animate().alpha(0f).setDuration(180).withEndAction {
      val attrs = window.attributes
      attrs.height = 1
      window.attributes = attrs
    }.start()
  }

  private fun scheduleAutoHide() {
    autoHideJob?.cancel()
    autoHideJob = activity.lifecycleScope.launch {
      delay(AUTO_HIDE_MS)
      collapseBar()
    }
  }

  // ---- MediaPlayer / SeekBar plumbing ----

  private fun startSeekBarUpdates(seekBar: SeekBar, timeView: TextView) {
    seekBarUpdateJob?.cancel()
    seekBarUpdateJob = activity.lifecycleScope.launch {
      while (true) {
        val mp = mediaPlayer ?: break
        try {
          if (mp.isPlaying) {
            val pos = mp.currentPosition
            seekBar.progress = pos
            timeView.text = formatTimeRange(pos, mp.duration)
          }
        } catch (_: IllegalStateException) {
          break
        }
        delay(250)
      }
    }
  }

  /** Stops playback, releases the MediaPlayer, and dismisses the bar. */
  fun stop() {
    seekBarUpdateJob?.cancel(); seekBarUpdateJob = null
    autoHideJob?.cancel(); autoHideJob = null
    mediaPlayer?.let { mp ->
      try {
        if (mp.isPlaying) mp.stop()
      } catch (_: IllegalStateException) {
        // already stopped
      }
      mp.release()
    }
    mediaPlayer = null
    dialog?.let { d ->
      if (d.isShowing) {
        d.setOnDismissListener(null)
        d.dismiss()
      }
    }
    dialog = null
    contentView = null
  }

  /** Convenience alias for [stop]. Call from the activity's onDestroy(). */
  fun release() = stop()

  // ---- Helpers ----

  private fun formatTimeRange(currentMs: Int, totalMs: Int): String =
    "${formatTime(currentMs)} / ${formatTime(totalMs)}"

  private fun formatTime(ms: Int): String {
    val totalSeconds = ms / 1000
    val seconds = totalSeconds % 60
    val minutes = totalSeconds / 60
    return String.format("%d:%02d", minutes, seconds)
  }

  companion object {
    private const val AUTO_HIDE_MS = 4_000L
  }
}
