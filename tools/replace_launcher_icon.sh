#!/usr/bin/env bash
#
# Replaces the Android launcher icon with TafsirPular.png.
# Uses macOS's built-in `sips` for image resizing — no extra tools needed.
#
# Usage (from the project root):
#   bash replace_launcher_icon.sh                  # uses ./TafsirPular.png
#   bash replace_launcher_icon.sh path/to/logo.png # uses a different source
#
# What it does:
#   1. Backs up existing mipmap-*/ folders to /tmp/launcher_icons_backup_<timestamp>.
#   2. Generates resized PNGs at the 5 standard densities (48, 72, 96, 144, 192 px).
#   3. Saves each as ic_launcher.png, ic_launcher_round.png, and
#      ic_launcher_foreground.png in the matching mipmap-<density>/ folder.
#   4. Prints a verify line for each density.
#
# After running, rebuild with: ./gradlew :app:installMadaniDebug

set -euo pipefail

SRC="${1:-TafsirPular.png}"

if [ ! -f "$SRC" ]; then
  echo "ERROR: source image '$SRC' not found."
  echo "Pass the path as the first argument, or place TafsirPular.png in the project root."
  exit 1
fi

if ! command -v sips &>/dev/null; then
  echo "ERROR: 'sips' command not found. This script is macOS-only."
  exit 1
fi

# Quick check: is this a PNG?
file_type=$(file --brief --mime-type "$SRC")
if [[ "$file_type" != "image/png" ]]; then
  echo "WARNING: $SRC is detected as $file_type, not image/png."
  echo "Proceeding anyway, but you may get a non-PNG output."
fi

RES_DIR="app/src/main/res"
if [ ! -d "$RES_DIR" ]; then
  echo "ERROR: $RES_DIR not found. Run this from the quran_android project root."
  exit 1
fi

# Backup
TS=$(date +%s)
BACKUP_DIR="/tmp/launcher_icons_backup_$TS"
mkdir -p "$BACKUP_DIR"
for d in "$RES_DIR"/mipmap-*; do
  if [ -d "$d" ]; then
    cp -R "$d" "$BACKUP_DIR/"
  fi
done
echo "Backed up existing icons to: $BACKUP_DIR"
echo ""

# Density → size table (matches Android Studio Image Asset defaults)
declare -a DENSITY_SIZES=(
  "mdpi:48"
  "hdpi:72"
  "xhdpi:96"
  "xxhdpi:144"
  "xxxhdpi:192"
)

for entry in "${DENSITY_SIZES[@]}"; do
  density="${entry%:*}"
  size="${entry#*:}"
  out_dir="$RES_DIR/mipmap-$density"
  mkdir -p "$out_dir"

  # Resize once, then copy to the three filenames.
  sips -z "$size" "$size" "$SRC" --out "$out_dir/ic_launcher.png" >/dev/null
  cp "$out_dir/ic_launcher.png" "$out_dir/ic_launcher_round.png"
  cp "$out_dir/ic_launcher.png" "$out_dir/ic_launcher_foreground.png"

  echo "  mipmap-$density: $(ls -la "$out_dir/ic_launcher.png" | awk '{print $5}') bytes (${size}x${size})"
done

echo ""
echo "Done. Three files updated in each density folder:"
echo "  - ic_launcher.png         (legacy launcher icon)"
echo "  - ic_launcher_round.png   (legacy round launcher icon)"
echo "  - ic_launcher_foreground.png (adaptive icon foreground)"
echo ""
echo "Now rebuild:"
echo "  ./gradlew :app:installMadaniDebug"
