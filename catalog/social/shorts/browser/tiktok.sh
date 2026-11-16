# TikTok Studio scheduling helpers for Peak Mind shorts (Peak Mind Chrome profile, signed in as peakmindshow).
# Source after x.sh, from the repo root, once `.upload-tmp/posts.json` holds the approved dated posts.
# `tslot <n> <YYYY-MM-DD>` uploads .upload-tmp/yt-<nn>.mp4, types the X post text as the caption,
# schedules it for 12:00 on that date (browser time zone must be America/New_York) and confirms it in the content list.
tcap(){ python3 -c "import json;p=[x for x in json.load(open('.upload-tmp/posts.json')) if x['n']==int('$1')][0];open('.upload-tmp/tt.txt','w').write(p['x'])"
  $A eval "() => { const e = document.querySelector('.public-DraftEditor-content'); e.focus(); document.execCommand('selectAll', false); return 1 }" >/dev/null 2>&1; $A press Backspace >/dev/null; $A wait 400 >/dev/null
  first=1; while IFS= read -r line || [ -n "$line" ]; do [ $first = 0 ] && $A press Enter >/dev/null; first=0; [ -n "$line" ] && $A type "$line" >/dev/null; done < .upload-tmp/tt.txt
  $A wait 800 >/dev/null
  got=$($A eval "() => document.querySelector('.public-DraftEditor-content').innerText.replace(/\\s+/g, ' ').trim()" 2>&1 | head -1 | jv)
  want=$(python3 -c "import re;print(re.sub(r'\s+',' ',open('.upload-tmp/tt.txt').read()).strip())")
  [ "$got" = "$want" ] || { echo "caption mismatch: got [$got]" >&2; return 1; }; echo caption-ok; }
tprep(){ N=$1; MON=$2; DAYLABEL="$3"; EXP="$4"
  $A open "https://www.tiktok.com/tiktokstudio/upload" >/dev/null 2>&1; r=$(W 'button "Select video"' 20) || { echo "no upload button"; return 1; }
  up=0; for try in 1 2 3; do r=$(R 'button "Select video"') ; [ -n "$r" ] && $A upload @$r $PWD/.upload-tmp/yt-$(printf %02d $N).mp4 >/dev/null 2>&1
    for i in $(seq 1 30); do $A eval "() => document.body.innerText.includes('Uploaded')" 2>&1 | head -1 | grep -q true && { up=1; break; }; $A wait 1000 >/dev/null; done; [ $up = 1 ] && break; done
  [ $up = 1 ] || { echo "#$N upload failed"; return 1; }
  $A wait 1500 >/dev/null
  for b in Cancel "Got it"; do r=$(R "button \"$b\"") && $A click @$r >/dev/null && $A wait 600 >/dev/null; done
  tcap $N || return 1
  $A eval "() => { const h = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && e.textContent.trim() === 'When to post'); h.click(); return 1 }" >/dev/null 2>&1
  r=$(R 'radio "Schedule"') && $A click @$r >/dev/null 2>&1; $A wait 1500 >/dev/null
  r=$(R 'button "Allow"') && $A click @$r >/dev/null && $A wait 1500 >/dev/null
  C 'combobox "Select date"' 5 || return 1; $A wait 800 >/dev/null
  for i in 1 2; do r=$(R "button \"$DAYLABEL\"") && break; C 'button "Next month"' 3; $A wait 700 >/dev/null; done
  [ -n "$r" ] || { echo "day not found"; return 1; }; $A click @$r >/dev/null; $A wait 800 >/dev/null
  C 'combobox "Select time"' 5 || return 1; $A wait 800 >/dev/null; C 'option "Hours 12"' 3; $A wait 500 >/dev/null; C 'option "Minutes 00"' 3; $A wait 500 >/dev/null
  $A eval "() => { const h = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && e.textContent.trim() === 'When to post'); h.click(); return 1 }" >/dev/null 2>&1; $A wait 600 >/dev/null
  st=$($A eval "() => [[...document.querySelectorAll('[class*=Picker__value]')].map(e => e.textContent.trim()).join(' '), document.querySelector('input[value=schedule]').checked, [...document.querySelectorAll('button')].filter(b => b.offsetParent && /^(Post|Schedule)$/.test(b.innerText.trim())).map(b => b.innerText.trim()).join(',')].join(' | ')" 2>&1 | head -1 | jv)
  [ "$st" = "$EXP 12:00 | true | Schedule" ] || { echo "#$N STOPPED: $st"; return 1; }; echo "#$N ready: $st"; }
tsched(){ N=$1; DL="$2"; EXP="$3"; SHORT="$4"
  tprep $N 0 "$DL" "$EXP" || return 1
  $A wait 3000 >/dev/null
  $A eval "() => { const b = [...document.querySelectorAll('button')].filter(b => b.offsetParent && b.innerText.trim() === 'Schedule'); if (b.length !== 1) return 'n=' + b.length; b[0].click(); return 'clicked' }" 2>&1 | head -1 | grep -q clicked || { echo "#$N no single Schedule button"; return 1; }
  $A wait 15000 >/dev/null
  for i in 1 2 3; do got=$($A eval "() => document.body.innerText.replace(/\s+/g, ' ').includes('$SHORT, 12:00 PM (GMT-5)') ? 'yes' : 'no'" 2>&1 | head -1); echo "$got" | grep -q yes && { echo "#$N scheduled $SHORT 12:00 PM"; return 0; }; $A open "https://www.tiktok.com/tiktokstudio/content" >/dev/null 2>&1; $A wait 10000 >/dev/null; done
  echo "#$N NOT CONFIRMED"; return 1; }
tslot(){ IFS='|' read -r DL EXP SHORT <<< "$(python3 -c "import datetime as d;x=d.date.fromisoformat('$2');o=lambda n:str(n)+('th' if 11<=n%100<=13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th'));print(x.strftime('%A, %B ')+o(x.day)+', '+str(x.year)+'|'+x.strftime('%b')+' '+str(x.day)+', '+str(x.year)+'|'+x.strftime('%b')+' '+str(x.day))")"
  tsched $1 "$DL" "$EXP" "$SHORT"; }
