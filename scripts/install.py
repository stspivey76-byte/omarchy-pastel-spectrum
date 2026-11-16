#!/usr/bin/env python3
"""Install into user config only; keep a restorable copy of every changed file."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
from rainbow import patch
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--terminal',action='store_true',help='Install Fastfetch panel and Starship prompt')
p.add_argument('--rainbow-icons',action='store_true',help='Tint icons on a compatible existing custom bar')
p.add_argument('--no-apply',action='store_true',help='Write files without changing the running theme')
p.add_argument('--restore',metavar='BACKUP',type=Path,help='Restore files from a previous installer backup')
a=p.parse_args(); home=Path.home(); config=home/'.config'
if a.restore:
    backup=a.restore.resolve(); manifest=json.loads((backup/'manifest.json').read_text())
    for entry in reversed(manifest):
        target=home/entry['path']
        if entry['existed']:
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(backup/'files'/entry['path'],target)
        else: target.unlink(missing_ok=True)
    print('Files restored. Select your previous theme and restart the shell to apply.'); raise SystemExit(0)
if not a.no_apply and not shutil.which('omarchy'):
    p.error('Omarchy is required; --no-apply can stage files without a running desktop.')
writes={}
for src in (ROOT/'theme').rglob('*'):
    if src.is_file(): writes[config/'omarchy/themes/pastel-spectrum'/src.relative_to(ROOT/'theme')]=src.read_bytes()
writes[config/'omarchy/hooks/theme-set.d/pastel-spectrum-sync']=(ROOT/'scripts/theme-sync').read_bytes()
if a.terminal:
    for src in (ROOT/'terminal').rglob('*'):
        if src.is_file(): writes[config/src.relative_to(ROOT/'terminal')]=src.read_bytes()
if a.rainbow_icons:
    settings=json.loads((config/'omarchy/shell.json').read_text()); barid=settings['bar'].get('id','')
    if '/' in barid or barid in ('','..','.'):
        p.error('A compatible custom bar is required for --rainbow-icons.')
    bar=config/'omarchy/plugins'/barid/'Bar.qml'
    if not bar.is_file(): p.error('No compatible custom Bar.qml found. Install the theme without --rainbow-icons.')
    try: writes[bar]=patch(bar.read_text(),settings['bar']['layout']).encode()
    except ValueError as e: p.error(str(e))
backup=home/'.local/state/pastel-spectrum-installer'/str(time.time_ns()); backup.mkdir(parents=True)
manifest=[]
for target,content in writes.items():
    if target.is_symlink(): p.error('Refusing to replace symlink: '+str(target))
    rel=target.relative_to(home); existed=target.exists()
    if existed:
        saved=backup/'files'/rel; saved.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(target,saved)
    manifest.append({'path':str(rel),'existed':existed})
# Save recovery information before the first mutation.
(backup/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for target,content in writes.items():
    target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(content)
    if target.name=='pastel-spectrum-sync': target.chmod(0o755)
print('Backup:',backup,flush=True)
if not a.no_apply:
    subprocess.run(['omarchy','theme','set','pastel-spectrum'],check=True)
    if a.rainbow_icons: subprocess.run(['omarchy','restart','shell'],check=True)
print('Installed Pastel Spectrum.')
