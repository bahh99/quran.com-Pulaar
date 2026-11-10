package com.quran.labs.androidquran.ui.helpers

import android.app.Dialog
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.text.TextUtils
import android.view.Gravity
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import com.quran.labs.androidquran.R
import com.quran.labs.androidquran.ui.helpers.FulaniPlaybackViewModel.State
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Playback bar for Sheikh Kaala / Fulani audio.
 *
 * The [android.media.MediaPlayer] lives in [FulaniPlaybackViewModel], so audio keeps
 * playing across rotation. This controller only owns the activity-bound UI: call
 * [attach] from onCreate to (re)show the bar for a session in progress, and
 * [detach] from onDestroy. The bar is shown immediately and stays visible while a
 * track is active.
 */
class FulaniPlaybackController(private val activity: AppCompatActivity) {

  private val vm: FulaniPlaybackViewModel =
    ViewModelProvider(activity)[FulaniPlaybackViewModel::class.java]

  private var seekBarUpdateJob: Job? = null
  private var dialog: Dialog? = null

  private var labelView: TextView? = null
  private var timeView: TextView? = null
  private var statusView: TextView? = null
  private var seekBar: SeekBar? = null
  private var playPauseButton: Button? = null

  /** Starts a new track and shows the bar right away. */
  fun play(audioUrl: String, trackLabel: String) {
    showBar()
    vm.start(audioUrl, trackLabel)
    render()
  }

  /** Re-shows the bar after the activity is recreated, if a session is active. */
  fun attach() {
    if (vm.hasSession && dialog == null) {
      showBar()
      render()
    }
  }

  /** Detaches the UI without touching playback. Call from onDestroy. */
  fun detach() {
    vm.onChanged = null
    seekBarUpdateJob?.cancel(); seekBarUpdateJob = null
    dialog?.let { d ->
      d.setOnDismissListener(null)
      if (d.isShowing) d.dismiss()
    }
    dialog = null
    labelView = null; timeView = null; statusView = null; seekBar = null; playPauseButton = null
  }

  /** Stops playback and hides the bar. */
  fun stop() {
    vm.stop()
    detach()
  }

  /** Called from onDestroy: keeps audio across rotation, stops it on a real exit. */
  fun release() {
    detach()
    if (!activity.isChangingConfigurations) vm.stop()
  }

  // ---- UI ----

  private fun showBar() {
    detach()
    val context: Context = activity
    val density = context.resources.displayMetrics.density
    val padding = (14 * density).toInt()
    val halfPadding = padding / 2
    val edgeMargin = (8 * density).toInt()

    val outerFrame = LinearLayout(context).apply {
      orientation = LinearLayout.VERTICAL
      setPadding(edgeMargin, edgeMargin, edgeMargin, edgeMargin)
    }
    val card = LinearLayout(context).apply {
      orientation = LinearLayout.VERTICAL
      setPadding(padding, padding, padding, padding)
      background = GradientDrawable().apply {
        shape = GradientDrawable.RECTANGLE
        cornerRadius = 18 * density
        setColor(Color.parseColor("#F2202020"))
      }
    }

    val labelRow = LinearLayout(context).apply {
      orientation = LinearLayout.HORIZONTAL
      gravity = Gravity.CENTER_VERTICAL
    }
    labelView = TextView(context).apply {
      textSize = 14f
      maxLines = 1
      setTextColor(Color.WHITE)
      setTypeface(typeface, Typeface.BOLD)
      ellipsize = TextUtils.TruncateAt.END
      layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
    }
    labelRow.addView(labelView)
    timeView = TextView(context).apply {
      textSize = 12f
      setTextColor(Color.LTGRAY)
    }
    labelRow.addView(timeView)
    card.addView(labelRow)

    statusView = TextView(context).apply {
      textSize = 11f
      setTextColor(Color.parseColor("#AAAAAA"))
      setPadding(0, halfPadding / 2, 0, halfPadding)
    }
    card.addView(statusView)

    seekBar = SeekBar(context).apply { max = 0; progress = 0 }
    card.addView(seekBar)

    val buttonsRow = LinearLayout(context).apply {
      orientation = LinearLayout.HORIZONTAL
      gravity = Gravity.CENTER
      setPadding(0, halfPadding, 0, 0)
    }
    val buttonSize = (52 * density).toInt()
    playPauseButton = Button(context).apply {
      textSize = 18f
      setTextColor(Color.WHITE)
      background = GradientDrawable().apply {
        shape = GradientDrawable.OVAL
        setColor(Color.parseColor("#2E7D32"))
      }
      includeFontPadding = false
      setPadding(0, 0, 0, 0)
      minWidth = 0
      minimumWidth = 0
      minimumHeight = 0
      setOnClickListener { vm.togglePlayPause() }
    }
    buttonsRow.addView(playPauseButton, LinearLayout.LayoutParams(buttonSize, buttonSize))
    card.addView(buttonsRow)
    outerFrame.addView(card)

    seekBar?.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
      override fun onProgressChanged(sb: SeekBar?, progress: Int, fromUser: Boolean) {
        if (fromUser) {
          vm.seekTo(progress)
          timeView?.text = formatTimeRange(progress, vm.duration())
        }
      }
      override fun onStartTrackingTouch(sb: SeekBar?) {}
      override fun onStopTrackingTouch(sb: SeekBar?) {}
    })

    // Non-modal so the reader can still scroll/tap the page behind the bar.
    val d = Dialog(context)
    d.setContentView(outerFrame)
    d.setOnDismissListener { stop() }
    d.window?.let { window ->
      window.setFlags(
        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
      )
      window.setDimAmount(0f)
      window.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
      val attrs = window.attributes
      attrs.gravity = Gravity.BOTTOM
      attrs.width = ViewGroup.LayoutParams.MATCH_PARENT
      attrs.height = ViewGroup.LayoutParams.WRAP_CONTENT
      window.attributes = attrs
    }
    d.show()
    dialog = d

    vm.onChanged = { render() }
    startSeekBarUpdates()
  }

  private fun render() {
    val context: Context = activity
    labelView?.text = vm.label
    val status: String
    val buttonText: String
    when (vm.state) {
      State.LOADING -> {
        status = context.getString(R.string.fulani_loading_short)
        buttonText = context.getString(R.string.fulani_pause)
      }
      State.PLAYING -> {
        status = context.getString(R.string.fulani_playing_short)
        buttonText = context.getString(R.string.fulani_pause)
      }
      State.PAUSED -> {
        status = context.getString(R.string.fulani_playing_short)
        buttonText = context.getString(R.string.fulani_play)
      }
      State.FINISHED -> {
        status = context.getString(R.string.fulani_finished)
        buttonText = context.getString(R.string.fulani_play)
      }
      State.ERROR -> {
        status = vm.loadError?.let { context.getString(R.string.fulani_load_error, it) }
          ?: context.getString(R.string.fulani_playback_error, vm.errorWhat, vm.errorExtra)
        buttonText = context.getString(R.string.fulani_play)
      }
      State.IDLE -> return
    }
    statusView?.text = status
    playPauseButton?.text = buttonText
    val duration = vm.duration()
    seekBar?.max = duration
    timeView?.text = formatTimeRange(vm.position(), duration)
  }

  private fun startSeekBarUpdates() {
    seekBarUpdateJob?.cancel()
    seekBarUpdateJob = activity.lifecycleScope.launch {
      while (true) {
        if (vm.state == State.PLAYING) {
          val pos = vm.position()
          seekBar?.progress = pos
          timeView?.text = formatTimeRange(pos, vm.duration())
        }
        delay(250)
      }
    }
  }

  private fun formatTimeRange(currentMs: Int, totalMs: Int): String =
    "${formatTime(currentMs)} / ${formatTime(totalMs)}"

  private fun formatTime(ms: Int): String {
    val totalSeconds = ms / 1000
    return String.format("%d:%02d", totalSeconds / 60, totalSeconds % 60)
  }
}
