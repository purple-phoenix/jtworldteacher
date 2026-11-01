# Browser helpers for scheduling Peak Mind shorts in the Peak Mind Chrome profile (chrome-devtools-axi session peak-mind-social).
# Source from the repo root after `week.py stage <week.json>`; run only after Matt approves that week's kit.
# helpers for YouTube Studio scheduling in the Peak Mind Chrome profile
export CHROME_DEVTOOLS_AXI_SESSION=peak-mind-social CHROME_DEVTOOLS_AXI_USER_DATA_DIR=$HOME/.peak-mind-social-chrome CHROME_DEVTOOLS_AXI_HEADED=1 CHROME_DEVTOOLS_AXI_CHROME_ARGS="--disable-blink-features=AutomationControlled"
A=chrome-devtools-axi
R(){ $A snapshot 2>&1 | grep -E "$1" | sed -n "${2:-1}p" | grep -o 'g[0-9]*:[0-9_]*'; }
W(){ for i in $(seq 1 ${2:-20}); do r=$(R "$1" ${3:-1}); [ -n "$r" ] && { echo $r; return 0; }; $A wait 1000 >/dev/null; done; return 1; }
C(){ r=$(W "$@") || { echo "MISSING: $1" >&2; return 1; }; $A click @$r >/dev/null; }
fill_details(){ J=$(python3 -c "import json;p=[x for x in json.load(open('.upload-tmp/posts.json')) if x['n']==int('$1')][0];print(json.dumps({'title':p['title'],'desc':p['desc']}))")
  W 'textbox "Add a title' 30 >/dev/null || return 1
  $A eval "() => { const d = $J; const boxes = [...document.querySelectorAll('ytcp-uploads-dialog #textbox[contenteditable=true]')]; const put = (el, v) => { el.focus(); document.execCommand('selectAll', false); document.execCommand('insertText', false, v); }; put(boxes[0], d.title); put(boxes[1], d.desc); return boxes.length }" >/dev/null 2>&1
  $A eval "() => { const r = document.querySelector('tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]'); r.scrollIntoView(); r.click(); return r.getAttribute('aria-checked') }" 2>&1 | grep -q true || { echo "audience not set" >&2; return 1; }; }
to_visibility(){ for i in 1 2 3; do $A eval "() => { document.querySelector('ytcp-uploads-dialog #next-button').click(); return 1 }" >/dev/null 2>&1; $A wait 2000 >/dev/null; done; W 'heading "Visibility" level="1"' 20 >/dev/null || { echo "never reached Visibility" >&2; return 1; }; }
schedule(){ DATE="$1"
  [ "$($A eval "() => !!document.querySelector('ytcp-uploads-dialog #datepicker-trigger')?.offsetParent" 2>&1 | head -1)" = 'result: "true"' ] || { C 'button "Click to expand"' || return 1; $A wait 1500 >/dev/null; }
  cur=$($A eval "() => document.querySelector('ytcp-uploads-dialog #datepicker-trigger').innerText.trim()" 2>&1 | head -1)
  if ! echo "$cur" | grep -q "$DATE"; then
    $A eval "() => { document.querySelector('ytcp-uploads-dialog #datepicker-trigger').click(); return 1 }" >/dev/null 2>&1; $A wait 1500 >/dev/null
    $A eval "() => { const i = [...document.querySelectorAll('input')].find(i => /^[A-Z][a-z]{2} \\d{1,2}, \\d{4}$/.test(i.value) && i.offsetParent); i.focus(); i.select(); return 1 }" >/dev/null 2>&1
    $A type "$DATE" >/dev/null; $A press Enter >/dev/null; $A wait 1200 >/dev/null
  fi
  if ! $A eval "() => ([...document.querySelectorAll('ytcp-uploads-dialog input')].find(i => /^\\d{1,2}:\\d{2}\\s[AP]M$/.test(i.value)) || {}).value" 2>&1 | head -1 | grep -qE '12:00.PM'; then
    $A press Escape >/dev/null; $A wait 500 >/dev/null
    C 'textbox( focusable)?( focused)? value="[0-9]+:[0-9]+.[AP]M"' 8 || return 1; $A wait 1200 >/dev/null
    C 'option "12:00.PM"' 8 || return 1; $A wait 1000 >/dev/null
  fi
  chk=$($A eval "() => [document.querySelector('ytcp-uploads-dialog #datepicker-trigger').innerText.trim(), ([...document.querySelectorAll('ytcp-uploads-dialog input')].find(i => /^\\d{1,2}:\\d{2}\\s[AP]M$/.test(i.value)) || {}).value, document.querySelector('ytcp-uploads-dialog #title-textarea #textbox, ytcp-uploads-dialog #textbox').innerText.trim()].join(' | ')" 2>&1 | head -1)
  if echo "$chk" | grep -q "$DATE" && echo "$chk" | grep -qE '12:00.PM'; then
    $A eval "() => { document.querySelector('ytcp-uploads-dialog #done-button').click(); return 1 }" >/dev/null 2>&1
    W 'heading "Video scheduled"' 20 >/dev/null && echo "OK: $chk" || echo "UNCONFIRMED: $chk"; C 'button "Close"' 5 >/dev/null
  else echo "STOPPED: $chk"; return 1; fi; }
val(){ $A eval "() => ([...document.querySelectorAll('ytcp-uploads-dialog input')].find(i => /^\\d{1,2}:\\d{2}\\s[AP]M$/.test(i.value)) || {}).value" 2>&1 | head -1 | sed 's/result: //;s/"//g;s/\\//g'; }
set_noon(){ for cand in "12:00 PM" "11:00 AM" "1:00 PM" "11:45 AM" "12:15 PM"; do
    [ "$(val | tr '\342\200\257' ' ' | sed 's/[^0-9:APM]//g')" = "12:00PM" ] && return 0
    C 'textbox( focusable)?( focused)? value="[0-9]+:[0-9]+.[AP]M"' 5 || return 1; $A wait 800 >/dev/null
    $A eval "() => { const e = [...document.querySelectorAll('tp-yt-paper-item')].find(e => e.textContent.replace(/\\s+/g, ' ').trim() === '$cand'); e.click(); return 1 }" >/dev/null 2>&1; $A wait 800 >/dev/null
  done; [ "$(val | sed 's/[^0-9:APM]//g')" = "12:00PM" ]; }
set_date(){ DATE="$1"
  if [ "$($A eval "() => !!document.querySelector('ytcp-uploads-dialog #datepicker-trigger')?.offsetParent" 2>&1 | head -1)" != 'result: "true"' ]; then
    $A eval "() => { const b = [...document.querySelectorAll('ytcp-uploads-dialog [aria-label=\"Click to expand\"]')].filter(e => e.offsetParent).pop(); b.click(); return 1 }" >/dev/null 2>&1; $A wait 1500 >/dev/null; fi
  $A eval "() => document.querySelector('ytcp-uploads-dialog #datepicker-trigger').innerText.trim()" 2>&1 | grep -q "$DATE" && return 0
  $A eval "() => { document.querySelector('ytcp-uploads-dialog #datepicker-trigger').click(); return 1 }" >/dev/null 2>&1; $A wait 1500 >/dev/null
  $A eval "() => { const i = [...document.querySelectorAll('input')].find(i => /^[A-Z][a-z]{2} \\d{1,2}, \\d{4}$/.test(i.value) && i.offsetParent); i.focus(); i.select(); return 1 }" >/dev/null 2>&1
  $A type "$DATE" >/dev/null; $A press Enter >/dev/null; $A wait 1200 >/dev/null
  $A eval "() => document.querySelector('ytcp-uploads-dialog #datepicker-trigger').innerText.trim()" 2>&1 | grep -q "$DATE"; }
finish(){ DATE="$1"; set_date "$DATE" || { echo "date failed"; return 1; }; set_noon || { echo "time failed: $(val)"; return 1; }
  T=$($A eval "() => document.querySelector('ytcp-uploads-dialog').querySelector('#textbox').innerText.trim()" 2>&1 | head -1)
  $A eval "() => { document.querySelector('ytcp-uploads-dialog #done-button').click(); return 1 }" >/dev/null 2>&1
  for i in $(seq 1 20); do M=$($A eval "() => (document.body.innerText.match(/will be set to public on [^\\n]*/) || [''])[0]" 2>&1 | head -1); echo "$M" | grep -q 'public on' && break; $A wait 1000 >/dev/null; done
  echo "$M" | grep -q 'public on' && echo "OK: $M" || echo "UNCONFIRMED"
  $A press Escape >/dev/null; }
open_draft(){ TITLE="$1"; $A open "https://studio.youtube.com/channel/UCQN2NzD9rI_GwF8GKBaqVTw/videos/short" >/dev/null 2>&1; W 'checkbox "Select' 30 >/dev/null
  L=$($A snapshot 2>&1 | grep -E 'checkbox "Select [^a]|button "Edit draft"'); idx=$(echo "$L" | grep -n "checkbox \"Select $TITLE\"" | cut -d: -f1)
  ref=$(echo "$L" | sed -n "$((idx+1))p" | grep 'Edit draft' | grep -o 'g[0-9]*:[0-9_]*'); [ -n "$ref" ] || return 1; $A click @$ref >/dev/null; }
upload_new(){ $A open "https://studio.youtube.com/channel/UCQN2NzD9rI_GwF8GKBaqVTw/videos/upload?d=ud" >/dev/null 2>&1
  r=$(W 'button "Select files"' 30) || return 1; $A upload @$r "$1" 2>&1 | grep -i error; }
