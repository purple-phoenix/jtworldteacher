#!/bin/zsh
# Compose a Peak Mind "Oracular Broadside" episode cover from text-free source art.
# Recovered from the 2026-10-12 Codex session that produced the original six covers
# (.lavish/compose-covers.sh, final revision), with auto-fit added for long titles.
#
# usage: catalog/scripts/compose_peak_mind_cover.sh <source.png> <output.jpg> <MAIN TITLE> <SUBTITLE>
#   MAIN TITLE / SUBTITLE may contain \n for line breaks (use $'...' quoting).
set -euo pipefail

source_png="$1"
out_jpg="$2"
main_title="$3"
subtitle="$4"

serif_font="/System/Library/Fonts/Supplemental/BigCaslon.ttf"
condensed_font="/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
# Big Caslon only has old-style figures (descending 5, short 1); digits in a title are
# set in Baskerville's lining figures, scaled to Big Caslon's cap height.
digit_font="/System/Library/Fonts/Supplemental/Baskerville.ttc"
digit_scale=1105  # per mille: Caslon cap height 238.7 / Baskerville figure height 216
max_width=2560  # rule runs 180..2820; keep type inside it

# Largest pointsize <= $2 whose widest line fits max_width.
fit() {
  local text="$1" size="$2" spacing="$3" width
  while (( size > 60 )); do
    width=$(magick -font "$serif_font" -pointsize "$size" -interline-spacing "$spacing" \
      label:"$text" -format '%w' info:)
    (( width <= max_width )) && break
    size=$(( size - 5 ))
  done
  print -- "$size"
}

main_size=$(fit "$main_title" 330 -24)
# The original set kept one-line subtitles near 0.55 of the title size, two-line near 0.45.
if [[ "$subtitle" == *$'\n'* ]]; then sub_ratio=45; else sub_ratio=55; fi
sub_size=$(fit "$subtitle" $(( main_size * sub_ratio / 100 )) -18)

metric() {  # metric <font> <size> <text> <field>: advance width or descent from annotate metrics
  local out  # capture fully first: an early-exiting grep would SIGPIPE magick under pipefail
  out=$(magick -debug annotate xc:white -font "$1" -pointsize "$2" -annotate +0+0 "$3" null: 2>&1)
  print -- "$out" | grep -oE "$4: -?[0-9.]+" | head -1 | grep -oE -- '-?[0-9.]+$'
}

# Main title draw arguments. Default: one centered annotate, exactly as the original set.
main_args=(-fill '#8f2f2a' -stroke none -font "$serif_font" -pointsize "$main_size"
  -interline-spacing -24 -gravity south -annotate +0+500 "$main_title")
if [[ "$main_title" == *[0-9]* && "$main_title" != *$'\n'* ]]; then
  # Mixed runs on a shared baseline: where gravity-south +500 puts Big Caslon's baseline.
  digit_size=$(( main_size * digit_scale / 1000 ))
  descent=$(metric "$serif_font" "$main_size" "$main_title" descent)
  baseline=$(( 2500 + ${descent%.*} ))
  runs=("${(@f)$(print -- "$main_title" | grep -oE '[0-9]+|[^0-9]+')}")
  total=0; widths=()
  for run in "${runs[@]}"; do
    if [[ "$run" == [0-9]* ]]; then w=$(metric "$digit_font" "$digit_size" "$run" width)
    else w=$(metric "$serif_font" "$main_size" "$run" width); fi
    widths+=("${w%.*}"); total=$(( total + ${w%.*} ))
  done
  x=$(( 1500 - total / 2 ))
  main_args=(-fill '#8f2f2a' -stroke none +gravity)
  for i in {1..${#runs}}; do
    if [[ "${runs[$i]}" == [0-9]* ]]; then main_args+=(-font "$digit_font" -pointsize "$digit_size")
    else main_args+=(-font "$serif_font" -pointsize "$main_size"); fi
    main_args+=(-annotate "+${x}+${baseline}" "${runs[$i]}")
    x=$(( x + widths[$i] ))
  done
fi

test -f "$source_png"
[[ -e "$out_jpg" ]] && { print -u2 "refusing to overwrite $out_jpg"; exit 1; }

magick "$source_png" \
  -resize '3000x3000!' \
  -colorspace sRGB \
  -fill '#11100df2' -stroke none -draw 'rectangle 150,120 1190,390' \
  -fill '#c79b3b' -font "$condensed_font" -pointsize 118 -gravity northwest \
  -annotate +225+177 'PEAK MIND' \
  -fill '#e8dcc1f7' -stroke none -draw 'rectangle 0,1900 3000,3000' \
  -stroke '#11100d' -strokewidth 12 -draw 'line 180,1980 2820,1980' \
  "${main_args[@]}" \
  -fill '#11100d' -font "$serif_font" -pointsize "$sub_size" -interline-spacing -18 -gravity south \
  -annotate +0+128 "$subtitle" \
  -strip -sampling-factor 4:2:0 -quality 88 -type TrueColor "$out_jpg"

print "wrote $out_jpg (main ${main_size}pt, subtitle ${sub_size}pt)"
