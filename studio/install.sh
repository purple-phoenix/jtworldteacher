#!/bin/sh
# Explicitly run this to install or update the local running copy.
set -eu
studio_source=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 - "$studio_source" <<'PY'
import os
from pathlib import Path
import plistlib
import runpy
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape

source = Path(sys.argv[1])
config = runpy.run_path(str(source / 'server.py'))['load_config']()
app = Path(config['appDir'])
data = Path(config['dataDir'])
# Refuse overlapping code and data destinations, including resolved symlinks.
if app == source.resolve() or app.is_relative_to(data) or data.is_relative_to(app):
    raise SystemExit('App destination must be separate from data and the source checkout')
if source.resolve().is_relative_to(app):
    raise SystemExit('App destination must not contain the source checkout')
python = shutil.which(os.path.expanduser(config['pythonBin']))
if not python:
    raise SystemExit('Cannot find configured pythonBin')
app.mkdir(parents=True, exist_ok=True)
for name in ('server.py', 'studioctl.py'):
    shutil.copy2(source / name, app / name)
shutil.copytree(source / 'static', app / 'static', dirs_exist_ok=True)
plist = Path(config['launchAgent'])
log = Path(config['logFile'])
plist.parent.mkdir(parents=True, exist_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)
search_path = config.get('path', f'{Path.home()}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin')
search_path = ':'.join(os.path.expanduser(p) for p in search_path.split(':'))
replacements = {'PYTHON': python, 'SERVER': str(app / 'server.py'), 'APP': str(app),
                'LOG': str(log), 'PATH': search_path, 'CONFIG': config['configPath']}
text = (source / 'launchd/com.peakmind.studio.plist.template').read_text()
for key, value in replacements.items():
    text = text.replace('@@' + key + '@@', escape(value))
# Parse before writing so malformed paths or template errors cannot install a broken plist.
plistlib.loads(text.encode())
plist.write_text(text)
domain = f'gui/{os.getuid()}'
service = domain + '/com.peakmind.studio'
loaded = subprocess.run(['launchctl', 'print', service], capture_output=True).returncode == 0
if loaded:
    # Reload so config, Python, and log path changes also take effect on updates.
    subprocess.run(['launchctl', 'bootout', service], check=True)
subprocess.run(['launchctl', 'bootstrap', domain, str(plist)], check=True)
subprocess.run(['launchctl', 'kickstart', '-k', service], check=True)
print(f'Installed app: {app}\nData is separate: {data}\nLogs: {log}')
print(f'Local Studio: http://127.0.0.1:{config["port"]}')
print('Run this yourself to expose Studio on your tailnet:')
print(f'tailscale serve --bg --https={config["port"]} http://127.0.0.1:{config["port"]}')
PY
