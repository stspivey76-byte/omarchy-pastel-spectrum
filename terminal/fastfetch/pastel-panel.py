#!/usr/bin/env python3
"""Screenshot-inspired terminal panel, populated by Fastfetch's live data."""
import datetime, json, os, re, shutil, subprocess
from pathlib import Path
RESET='\033[0m'
COLORS=['#ed70df','#efd2aa','#91c69b','#80b8eb','#b8acd5']
def ink(s,c):
 r,g,b=bytes.fromhex(c.lstrip('#')); return f'\033[38;2;{r};{g};{b}m{s}{RESET}'
def run(args):
 try: return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=4).strip()
 except (OSError,subprocess.SubprocessError): return 'Unavailable'
raw=run(['fastfetch','--config','none','--structure','OS:Kernel:Display:CPU:GPU:Memory:Swap:Disk:Battery:Shell:Terminal:Packages:Uptime','--format','json'])
try: data={x['type']:x.get('result') for x in json.loads(raw)}
except (ValueError,TypeError): data={}
def get(k): return data.get(k) or {}
def first(k): return next(iter(data.get(k) or []),{})
W=min(72,max(44,shutil.get_terminal_size((80,24)).columns-4)); LEFT=14
ansi=re.compile(r'\x1b\[[0-9;]*m')
def fit(s,n):
 plain=ansi.sub('',s)
 if len(plain)>n: return plain[:n-1]+'…'
 return s+' '*(n-len(plain))
def outer(s): print(' '+ink('│',COLORS[3])+fit(s,W-2)+ink('│',COLORS[3]))
def edge(l,m,r,c): return ink(l+m+r,c)
def section(title,rows,c):
 def boxed(s): outer(' '+s+' ')
 span=W-6; label=' '+title+' '; n=(span-len(label))//2
 boxed(edge('┌','─'*n+label+'─'*(span-len(label)-n),'┐',c))
 for label,value in rows:
  boxed(ink('│',c)+ink(fit(' '+label,LEFT),c)+ink('│',c)+' '+fit(str(value),W-LEFT-9)+' '+ink('│',c))
 boxed(edge('└','─'*LEFT+'┴'+'─'*(W-LEFT-7),'┘',c))
def bar(p):
 p=max(0,min(100,p)); n=round(p/10)
 blocks=''.join(ink('█',COLORS[min(4,i//2)]) for i in range(n))+' '*(10-n)
 return ink('▕',COLORS[3])+blocks+ink('▏',COLORS[3])+f' ({p:.0f}%)'
def ratio(x): return 100*x.get('used',0)/max(1,x.get('total',0))
font={
'O':[' ███ ','█   █','█   █','█   █',' ███ '],
'M':['█   █','██ ██','█ █ █','█   █','█   █'],
'A':[' ███ ','█   █','█████','█   █','█   █'],
'R':['████ ','█   █','████ ','█  █ ','█   █'],
'C':[' ████','█    ','█    ','█    ',' ████'],
'H':['█   █','█   █','█████','█   █','█   █'],
'Y':['█   █',' █ █ ','  █  ','  █  ','  █  ']}
print()
for i,c in enumerate(COLORS):
 line=' '.join(font[x][i] for x in 'OMARCHY')
 print(' '+ink(line.center(W),c))
print()
print(' '+edge('┌','─'*(W-2),'┐',COLORS[3]))
osinfo=get('OS'); kernel=get('Kernel')
section('OS',[(' OS',f"{osinfo.get('prettyName','Linux')} {osinfo.get('versionID','')} {kernel.get('architecture','')}"),(' Kernel',f"Linux {kernel.get('release','Unknown')}")],COLORS[2])
outer('')
display=first('Display').get('output',{}); cpu=get('CPU'); gpu=first('GPU'); disk=next((x for x in data.get('Disk',[]) if x['mountpoint']=='/'),{}) .get('bytes',{})
swap=data.get('Swap') or []; swap={'used':sum(x['used'] for x in swap),'total':sum(x['total'] for x in swap)}
rows=[('󰍹 Display',f"{display.get('width','?')}×{display.get('height','?')} @ {display.get('refreshRate',0):g} Hz"),(' CPU',f"{cpu.get('cpu','Unknown')} ({cpu.get('cores',{}).get('logical','?')})"),('󰢮 GPU',f"{gpu.get('vendor','')} {gpu.get('name','Unknown')}"),('󰘚 RAM',bar(ratio(get('Memory')))),('󰓡 SWAP',bar(ratio(swap))),('󰋊 Storage',bar(100*(disk.get('total',1)-disk.get('free',0))/max(1,disk.get('total',1))))]
bat=first('Battery')
if bat: rows.append(('󰁹 Battery',bar(bat.get('capacity',0))+' '+', '.join(bat.get('status',[]))))
section('Hardware',rows,COLORS[3]); outer('')
shell=get('Shell'); terminal=get('Terminal')
# The nested Fastfetch process sees its caller; walk ancestors to find the emulator.
pid=os.getpid()
for _ in range(16):
 try:
  proc=Path('/proc')/str(pid)
  name=(proc/'comm').read_text().strip()
  if name in ('foot','footclient','ghostty','kitty','alacritty'):
   terminal={'prettyName':name}; break
  pid=int(next(x.split()[1] for x in (proc/'status').read_text().splitlines() if x.startswith('PPid:')))
  if pid<=1: break
 except (OSError,ValueError,StopIteration): break
shelltext=f"{shell.get('prettyName','')} {shell.get('version','')}" if shell.get('exeName')=='fish' else run(['fish','--version']).replace('fish, version','fish')
section('Terminal',[(' Shell',shelltext),(' Terminal',(os.environ.get('TERM_PROGRAM') or ('Foot' if os.environ.get('TERM','').startswith('foot') else terminal.get('prettyName','Unknown')))),('󰏖 Packages',f"{get('Packages').get('all','?')} (pacman)")],COLORS[1]); outer('')
rows=[]
for label,cmd in [(' Clang',['clang','--version']),(' Python',['python3','--version']),(' Git',['git','--version'])]:
 if shutil.which(cmd[0]): rows.append((label,run(cmd).splitlines()[0]))
section('Development',rows,COLORS[0]); outer('')
minutes=int(get('Uptime').get('uptime',0)//60000)
birth=run(['stat','-c','%W','/'])
try:
 date=datetime.datetime.fromtimestamp(int(birth)); age=f'{date:%Y-%m-%d} ({(datetime.datetime.now()-date).days} days)'
except (ValueError,OverflowError): age='Unknown'
section('Uptime',[('󰥔 Uptime',f'{minutes//60} hours, {minutes%60} mins'),('󰃭 OS Age',age)],COLORS[4])
print(' '+edge('└','─'*(W-2),'┘',COLORS[3])); print()
