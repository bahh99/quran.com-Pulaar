package com.quran.labs.androidquran.ui.helpers

import android.media.MediaPlayer
import androidx.lifecycle.ViewModel

/**
 * Owns the Fulani/Sheikh Kaala [MediaPlayer] so playback survives activity
 * recreation (e.g. portrait <-> landscape rotation). The activity-bound UI lives in
 * [FulaniPlaybackController]; this class holds no view or activity references
 * beyond the [onChanged] callback, which the controller clears on detach.
 */
class FulaniPlaybackViewModel : ViewModel() {

  enum class State { IDLE, LOADING, PLAYING, PAUSED, FINISHED, ERROR }

  var player: MediaPlayer? = null
    private set
  var label: String = ""
    private set
  var state: State = State.IDLE
    private set
  var loadError: String? = null
    private set
  var errorWhat: Int = 0
    private set
  var errorExtra: Int = 0
    private set

  /** Set by the attached UI; invoked on the main thread whenever [state] changes. */
  var onChanged: (() -> Unit)? = null

  val hasSession: Boolean get() = state != State.IDLE

  fun start(url: String, trackLabel: String) {
    stop()
    label = trackLabel
    state = State.LOADING
    val mp = MediaPlayer()
    player = mp
    try {
      mp.setDataSource(url)
    } catch (e: Exception) {
      mp.release()
      player = null
      loadError = e.message ?: ""
      state = State.ERROR
      onChanged?.invoke()
      return
    }
    mp.setOnPreparedListener { ready ->
      ready.start()
      state = State.PLAYING
      onChanged?.invoke()
    }
    mp.setOnCompletionListener {
      state = State.FINISHED
      onChanged?.invoke()
    }
    mp.setOnErrorListener { _, what, extra ->
      errorWhat = what
      errorExtra = extra
      releasePlayer()
      state = State.ERROR
      onChanged?.invoke()
      true
    }
    onChanged?.invoke()
    mp.prepareAsync()
  }

  fun togglePlayPause() {
    val mp = player ?: return
    try {
      when (state) {
        State.PLAYING -> { mp.pause(); state = State.PAUSED }
        State.PAUSED, State.FINISHED -> { mp.start(); state = State.PLAYING }
        else -> return
      }
      onChanged?.invoke()
    } catch (_: IllegalStateException) {
      // not prepared yet
    }
  }

  fun seekTo(ms: Int) {
    try {
      player?.seekTo(ms)
    } catch (_: IllegalStateException) {
      // not prepared yet
    }
  }

  fun position(): Int = try { player?.currentPosition ?: 0 } catch (_: IllegalStateException) { 0 }

  fun duration(): Int = try { player?.duration ?: 0 } catch (_: IllegalStateException) { 0 }

  /** Stops playback and clears the session. */
  fun stop() {
    releasePlayer()
    state = State.IDLE
    loadError = null
  }

  private fun releasePlayer() {
    player?.let { mp ->
      try {
        if (mp.isPlaying) mp.stop()
      } catch (_: IllegalStateException) {
        // already stopped
      }
      mp.release()
    }
    player = null
  }

  override fun onCleared() {
    onChanged = null
    stop()
  }
}
