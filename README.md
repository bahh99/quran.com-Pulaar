<div align="center">

<img src="app/icon_source/icon_source.png" alt="Quran et Tafsir - Pular logo" width="180"/>

# Quran et Tafsir - Pular

A free, open-source Android app for reading the Quran with **Tafsir in Pular (Fulani)**, including audio by Sheikh Abdullah Kaala.

[![Download](https://img.shields.io/badge/Download-latest%20release-2E7D32?logo=android)](https://github.com/bahh99/quran.com-Pulaar/releases/latest)

</div>

## What it does

* Quran pages (Madani) with Tafsir in Pular
* Fulani audio you can pick per surah and per section, with a playback bar that stays on screen
* Audio keeps playing when you rotate the phone
* Free, with no ads

## Install

1. Open the [latest release](https://github.com/bahh99/quran.com-Pulaar/releases/latest) on your Android phone.
2. Download the `.apk` file.
3. Open it. If Android asks, allow "Install unknown apps" for your browser or file manager.

## Support the project

Hosting the audio costs money every month. If the app is useful to you, you can help cover the hosting costs through PayPal: *(link coming soon)*. The project is non-profit.

## Build it yourself

```bash
./gradlew assembleMadaniDebug     # debug build
./release.sh                      # signed release build (needs your own signing key)
```

The release script expects `signing/keystore.properties` with `STORE_FILE`, `STORE_PASSWORD`, `KEY_ALIAS` and `KEY_PASSWORD`. Keep that file and your key private and out of git.

## Feedback and collaboration

Found a bug or want to help? Open an issue or a pull request on this repository.

## About this project

Quran et Tafsir - Pular is a fork of [Quran for Android](https://github.com/quran/quran_android) and is released under the same GPL 3 licence. Thank you to the original developers and contributors. The text below is from the original project.

---

## Credits

* madani images from [quran images project](https://github.com/quran/quran.com-images) on github.
* qaloon images used with permission of Nous Memes Editions Et Diffusion (Tunisia).
* naskh images used with permission of SHL Info Systems.
* translation, tafsir and Arabic data come from [quranenc](https://quranenc.com) and [King Saud University](https://quran.ksu.edu.sa). a small number of translations also come from [tanzil](http://tanzil.net).

## Contributing

If you'd like to contribute, please take a look at the [PRs Welcome](https://github.com/quran/quran_android/issues?q=is%3Aissue+is%3Aopen+label%3A%22PRs+Welcome%22) label on the issue tracker. For new features, please open an issue to discuss it before beginning implementation.

Use [`quran_android-code_style.xml`](https://github.com/quran/quran_android/blob/main/quran_android-code_style.xml) for Android Studio / IntelliJ code styles. Import it by copying it to the Android Studio/IntelliJ IDEA codestyles folder. For Android Studio, that folder is located at `~/.AndroidStudio[Version]/config/codestyles` (the root folder name may differ depending on the host machine and Android Studio version, but the rest of the path should be same). After copying the `quran_android-code_style.xml`, go to Code Style preferences screen and choose `quran_android-code_style` from Code Style Schemes.

Please set your Android studio kotlin code style based on [Kotlin Coding Conventions](https://kotlinlang.org/docs/reference/coding-conventions.html). You can configure it from menu Settings | Editor | Code Style | Kotlin, click on "Set from…" link in the upper right corner, and select "Predefined style / Kotlin style guide" from the menu.

May Allah reward all the awesome [Contributors and Translators](https://github.com/quran/quran_android/blob/main/CONTRIBUTORS.md).


## Setup

### Command Line

You can build Quran from the command line by running `./gradlew assembleMadaniDebug`.

### Android Studio / IntelliJ

Choose "Import Project," and choose the `build.gradle` file from the top level directory. Under "Build Variants" (a tab on the left side), choose "madaniDebug."

## Using Quran for Android code in other projects

The intention behind open sourcing Quran for Android is two fold - first, to allow developers to help contribute to the app, thus speeding up the development of new features and ideas. Second, to give back to the community and serve as a code reference.

Quran for Android costs money to run - all the data (pages, audio files, and translations) are hosted on servers that people volunteer their money to pay for every month. Moreover, the data itself is the work of various scholars, organizations, or reciters, many of whom provide this data free for usage for the benefit of the ummah.

Therefore, people planning on taking this project and profiting from it (by way of ads, in app purchases, etc) are in fact stealing from the work of the contributors of this project, and from the people who volunteer to pay for the servers (since they increase the bandwidth costs on them instead of covering them themselves).

Please keep use of this code for non-profit purposes only. Also, please note that the project is under the GPL 3 license, which requires that modifications to this code be open sourced as well. Please note that the data is licensed under the various licenses of the data's authors (typically, this is [CC BY-NC-ND](https://creativecommons.org/licenses/by-nc-nd/2.0/), but may differ depending on the source of the data).


## Open Source Projects Used

* [AndroidX](https://developer.android.com/jetpack/androidx/)
* [Kotlin](https://kotlinlang.org)
* [Material Design Components](https://github.com/material-components/material-components-android)
* [AndroidSlidingUpPanel](https://github.com/umano/AndroidSlidingUpPanel)
* [OkHttp](https://github.com/square/okhttp)
* [RxJava 2](https://github.com/ReactiveX/RxJava)
* [RxAndroid](https://github.com/ReactiveX/RxAndroid)
* [Moshi](https://github.com/square/moshi)
* [Dagger2](https://google.github.io/dagger/)
* [Timber](https://github.com/JakeWharton/timber)
* [dnsjava](http://dnsjava.org)
* [NumberPicker](https://github.com/ShawnLin013/NumberPicker)
