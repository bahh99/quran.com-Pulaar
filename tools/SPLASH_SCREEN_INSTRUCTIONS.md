# Splash screen — three small changes

Adds a system splash screen showing the TafsirPular logo before the launcher
activity loads. Uses the AndroidX `core-splashscreen` compat library, which
works on API 23+ (your minSdk should be fine).

---

## Step 1 — Verify the dependency

Check `app/build.gradle.kts` (or `app/build.gradle` if Groovy) for the
splash-screen library. From the project root:

```bash
grep -n "core-splashscreen\|splashscreen" app/build.gradle.kts 2>/dev/null \
  || grep -n "core-splashscreen\|splashscreen" app/build.gradle 2>/dev/null
```

- If you see a line like `implementation("androidx.core:core-splashscreen:...")`,
  you're set — skip to Step 2.
- If nothing prints, add this line inside the `dependencies { ... }` block in
  `app/build.gradle.kts`:

```kotlin
  implementation("androidx.core:core-splashscreen:1.0.1")
```

(or for Groovy `build.gradle`: `implementation 'androidx.core:core-splashscreen:1.0.1'`)

Then run a quick sync from Android Studio (or `./gradlew :app:dependencies` to verify).

---

## Step 2 — Add the splash theme

Open `app/src/main/res/values/themes.xml` (or `styles.xml`, depending on this
project's convention) and add this style anywhere inside `<resources>`:

```xml
<!-- Splash screen theme shown before the launcher activity. -->
<style name="Theme.TafsirPular.Starting" parent="Theme.SplashScreen">
    <!-- Background colour visible during splash. Adjust as you like. -->
    <item name="windowSplashScreenBackground">@android:color/white</item>
    <!-- The logo. Uses your launcher icon foreground we already generated. -->
    <item name="windowSplashScreenAnimatedIcon">@mipmap/ic_launcher_foreground</item>
    <!-- Theme to apply after the splash dismisses. Replace with your real app theme. -->
    <item name="postSplashScreenTheme">@style/Theme.QuranAndroid</item>
</style>
```

**Important:** `postSplashScreenTheme` must point at the theme your launcher
activity normally uses. To find that theme, look in `AndroidManifest.xml` for
the activity that has `<category android:name="android.intent.category.LAUNCHER" />`
and check what `android:theme="@style/..."` it currently uses. Replace
`Theme.QuranAndroid` above with that exact name.

If you can't easily find it, run:

```bash
grep -B1 "LAUNCHER" app/src/main/AndroidManifest.xml
```

---

## Step 3 — Apply the theme to the launcher activity

In `app/src/main/AndroidManifest.xml`, find the activity tag that contains
the launcher intent filter. It probably looks like this:

```xml
<activity
    android:name=".QuranDataActivity"
    android:theme="@style/Theme.QuranAndroid"
    ... >
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
</activity>
```

Change its `android:theme` attribute to:

```xml
    android:theme="@style/Theme.TafsirPular.Starting"
```

That's it for the basics. The system splash will now show the TafsirPular logo
with a white background, then fade into the regular app theme automatically.

---

## Step 4 (optional but recommended) — `installSplashScreen()` in the launcher

For the splash to integrate cleanly across all Android versions, the launcher
activity should call `installSplashScreen()` as its very first line of
`onCreate()`. Open the launcher activity (likely `QuranDataActivity.kt`) and
add this at the top of `onCreate()`:

```kotlin
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
// ...

override fun onCreate(savedInstanceState: Bundle?) {
    installSplashScreen()
    super.onCreate(savedInstanceState)
    // ... existing onCreate body
}
```

Without this line, the splash still shows but doesn't transition as smoothly
on API 31+ devices.

---

## Step 5 — Rebuild and test

```bash
./gradlew :app:installMadaniDebug
```

After install, fully close the app (swipe it away from recents), then launch
it from the home screen. You should see the TafsirPular icon centred on a
white screen briefly before the main app loads.

---

## Tweaks

- **Background colour.** Change `windowSplashScreenBackground` to any colour
  resource. For example `@color/black` for a dark splash. Make sure the
  contrast against your logo works.
- **Icon size.** The system splash applies a circular mask. If your logo gets
  cropped, the foreground bitmap (`ic_launcher_foreground.png`) should have
  about a third of its content inside the central 66% "safe zone". You can
  regenerate using a version of TafsirPular with extra padding around the
  edges.
- **Animated icon (API 31+).** You can use a `<animated-vector>` drawable for
  `windowSplashScreenAnimatedIcon` instead of a static PNG, if you want a
  short logo animation on Android 12+. Cosmetic only.
- **Splash duration.** By default the splash is shown only while the activity
  is preparing. If you want to hold it longer (e.g. while data loads), use
  `splashScreen.setKeepOnScreenCondition { stillLoading }` in the launcher
  activity after `installSplashScreen()`.
