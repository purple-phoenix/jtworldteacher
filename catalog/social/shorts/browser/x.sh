# Browser helpers for scheduling Peak Mind shorts in the Peak Mind Chrome profile (chrome-devtools-axi session peak-mind-social).
# Source from the repo root after `week.py stage <week.json>`; run only after Matt approves that week's kit.
source catalog/social/shorts/browser/youtube.sh
xtype(){ python3 -c "import json;p=[x for x in json.load(open('.upload-tmp/posts.json')) if x['n']==int('$1')][0];open('.upload-tmp/xtext.txt','w').write(p['x'])"
  $A eval "() => { const e = document.querySelector('[data-testid=tweetTextarea_0]'); e.click(); e.focus(); return 1 }" >/dev/null 2>&1; $A wait 500 >/dev/null
  first=1; while IFS= read -r line || [ -n "$line" ]; do [ $first = 0 ] && $A press Enter >/dev/null; first=0; [ -n "$line" ] && $A type "$line" >/dev/null; done < .upload-tmp/xtext.txt
  got=$($A eval "() => document.querySelector('[data-testid=tweetTextarea_0]').innerText.replace(/\\s+/g, ' ').trim()" 2>&1 | head -1 | jv)
  want=$(python3 -c "import re;print(re.sub(r'\s+',' ',open('.upload-tmp/xtext.txt').read()).strip())")
  if [ "$got" != "$want" ] && [ "${want:0:1}" = '"' ] && [ "$got" = "${want:1}" ]; then
    # X drops a typed opening quote; put it back at the start of the text
    $A eval "() => { const e = document.querySelector('[data-testid=tweetTextarea_0]'); const n = document.createTreeWalker(e, NodeFilter.SHOW_TEXT).nextNode(); const r = document.createRange(); r.setStart(n, 0); r.collapse(true); getSelection().removeAllRanges(); getSelection().addRange(r); e.focus(); document.execCommand('insertText', false, String.fromCharCode(34)); return 1 }" >/dev/null 2>&1; $A wait 500 >/dev/null
    got=$($A eval "() => document.querySelector('[data-testid=tweetTextarea_0]').innerText.replace(/\\s+/g, ' ').trim()" 2>&1 | head -1 | jv)
  fi
  [ "$got" = "$want" ] || { echo "text mismatch: got [$got]" >&2; return 1; }; }
xset(){ $A eval "() => { const want = {Month: '11', Day: '$1', Year: '2026', Hour: '12', Minute: '0', 'AM/PM': 'pm'}; for (const s of document.querySelectorAll('select')) { const lab = document.getElementById(s.getAttribute('aria-labelledby')).textContent; const v = want[lab]; if (v === undefined) continue; Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(s, v); s.dispatchEvent(new Event('change', {bubbles: true})); } return 1 }" >/dev/null 2>&1; }
jv(){ python3 -c "import json,sys;l=sys.stdin.readline();print(json.loads(json.loads(l[len('result: '):])) if l.startswith('result: ') else '')"; }
summary(){ $A eval "() => (document.body.innerText.match(/Will send on[^\\n]*/) || [''])[0]" 2>&1 | head -1 | jv; }
xfinish(){ N=$1; DAY=$2; EXPECT="$3"
  [ -n "$($A eval "() => document.querySelectorAll('select').length || ''" 2>&1 | head -1 | jv)" ] || { $A eval "() => { document.querySelector('[data-testid=scheduleOption]').click(); return 1 }" >/dev/null 2>&1; $A wait 2000 >/dev/null; }
  xset $DAY; $A wait 800 >/dev/null; s=$(summary); [ "$s" = "Will send on $EXPECT at 12:00 PM" ] || { echo "#$N STOPPED: '$s'"; return 1; }
  $A eval "() => { document.querySelector('[data-testid=scheduledConfirmationPrimaryAction]').click(); return 1 }" >/dev/null 2>&1; $A wait 1500 >/dev/null
  for i in $(seq 1 60); do st=$($A eval "() => { const b = document.querySelector('[data-testid=tweetButton]'); return b.innerText.trim() + '|' + (b.getAttribute('aria-disabled') || 'false') }" 2>&1 | head -1); echo "$st" | grep -q 'Schedule|false' && break; $A wait 1000 >/dev/null; done
  echo "$st" | grep -q 'Schedule|false' || { echo "#$N button not ready: $st"; return 1; }
  $A eval "() => { document.querySelector('[data-testid=tweetButton]').click(); return 1 }" >/dev/null 2>&1
  for i in $(seq 1 15); do m=$($A eval "() => (document.body.innerText.match(/Your post will be sent on[^\\n]*/) || [''])[0]" 2>&1 | head -1); echo "$m" | grep -q 'will be sent' && break; $A wait 1000 >/dev/null; done
  echo "#$N: $m"; }
xpost(){ N=$1
  $A open "https://x.com/compose/post" >/dev/null 2>&1; r=$(W 'button "Add photos or video"' 20) || { echo "#$N no composer"; return 1; }
  ok=0; for try in 1 2 3; do r=$($A snapshot 2>&1 | grep -E 'button "Add photos or video"' | tail -1 | grep -o 'g[0-9]*:[0-9_]*'); $A upload @$r $PWD/.upload-tmp/x-$N.mp4 >/dev/null 2>&1
    W 'slider "video time scrubber"' 30 >/dev/null && { ok=1; break; }; done
  [ $ok = 1 ] || { echo "#$N video did not attach"; return 1; }
  xtype $N || return 1; xfinish "$@"; }
