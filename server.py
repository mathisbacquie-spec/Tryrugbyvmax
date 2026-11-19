import asyncio, json, random, secrets, string, time
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app=FastAPI()
PLAYERS=json.loads(Path(__file__).with_name('players.json').read_text(encoding='utf-8'))
rooms={}
FORWARD=('pilier','talonneur','ligne','flanker','number 8','lock','prop','hooker','forward')

def forward(p): return any(x in p['poste'].lower() for x in FORWARD)
def new_deck():
    a=random.sample([p for p in PLAYERS if forward(p)],6)
    b=random.sample([p for p in PLAYERS if not forward(p)],6)
    return random.sample(a+b,12)
def public(r):
    return {'type':'state','code':r['code'],'started':r['started'],'connected':[x is not None for x in r['sockets']],'names':r['names'],
      'index':r['index'],'total':12,'player':r['deck'][r['index']] if r['started'] and r['index']<12 else None,
      'budgets':r['budgets'],'teams':r['teams'],'turn':r['turn'],'price':r['price'],'leader':r['leader'],
      'deadline':r['deadline'],'done':r['done'],'finished':r['finished'],'notice':r['notice']}
async def broadcast(r):
    msg=json.dumps(public(r),ensure_ascii=False)
    for ws in r['sockets']:
        if ws:
            try: await ws.send_text(msg)
            except Exception: pass
async def error(ws,message): await ws.send_json({'type':'error','message':message})
def clean_name(value):
    return ' '.join(str(value or '').strip().split())[:20]

def eligible(r,i): return len(r['teams'][i])<6 and r['budgets'][i]>=1

def settle(r):
    i=r['leader']
    if i is not None and eligible(r,i) and r['budgets'][i]>=r['price']:
        r['budgets'][i]-=r['price'];r['teams'][i].append(r['deck'][r['index']]);r['notice']=f"Joueur {i+1} remporte {r['deck'][r['index']]['nom']} pour {r['price']} €"
    r['done']=True;r['deadline']=None

def advance(r):
    r['price']=0;r['leader']=None;r['done']=False
    if r['index']>=12 or not (eligible(r,0) or eligible(r,1)):
        r['finished']=True;r['deadline']=None;r['notice']='Partie terminée';return
    r['turn']=r['index']%2
    if not eligible(r,r['turn']): r['turn']=1-r['turn']
    if not eligible(r,1-r['turn']):
        r['price']=1;r['leader']=r['turn'];settle(r);return
    r['deadline']=time.time()+15;r['notice']=f"Au tour du joueur {r['turn']+1}"

def bid(r):
    i=r['turn']
    if r['done'] or r['finished'] or not eligible(r,i) or r['budgets'][i]<r['price']+1:return False
    r['price']+=1;r['leader']=i;r['turn']=1-i
    if not eligible(r,r['turn']) or r['budgets'][r['turn']]<r['price']+1: settle(r)
    else:r['deadline']=time.time()+15;r['notice']=f"Au tour du joueur {r['turn']+1}"
    return True

async def clock(r):
    try:
        while rooms.get(r['code']) is r:
            await asyncio.sleep(.2)
            async with r['lock']:
                if not r['started'] or r['done'] or r['finished'] or r['deadline'] is None:continue
                if time.time()<r['deadline']:continue
                if r['price']==0:bid(r) # opening bid mandatory
                else:settle(r) # timeout means pass
                await broadcast(r)
    except asyncio.CancelledError:pass

@app.get('/')
async def home():return FileResponse(Path(__file__).with_name('index.html'))

@app.websocket('/ws')
async def websocket(ws:WebSocket):
    await ws.accept();r=None;seat=None
    try:
        while True:
            msg=await ws.receive_json();action=msg.get('action')
            if r is None:
                if action=='create':
                    name=clean_name(msg.get('name'))
                    if not name:
                        await error(ws,'Entre ton pseudo avant de créer un salon.');continue
                    code=''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(6))
                    while code in rooms:code=''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(6))
                    r={'code':code,'sockets':[ws,None],'started':False,'deck':new_deck(),'index':0,'budgets':[20,20],
                       'teams':[[],[]],'names':[name,None],'turn':0,'price':0,'leader':None,'deadline':None,'done':False,'finished':False,
                       'notice':'En attente du joueur 2','lock':asyncio.Lock()}
                    rooms[code]=r;seat=0;r['clocktask']=asyncio.create_task(clock(r))
                elif action=='join':
                    code=str(msg.get('code','')).strip().upper();r=rooms.get(code)
                    name=clean_name(msg.get('name'))
                    if not name:
                        r=None;await error(ws,'Entre ton pseudo avant de rejoindre un salon.');continue
                    if not r or r['sockets'][1] is not None or r['started']:
                        r=None;await error(ws,'Salon introuvable, déjà complet ou partie déjà commencée.');continue
                    seat=1;r['sockets'][1]=ws;r['names'][1]=name;r['notice']='Les deux joueurs sont prêts'
                else:
                    await error(ws,'Crée ou rejoins un salon.');continue
                await ws.send_json({'type':'seat','seat':seat,'code':r['code']})
                await broadcast(r);continue
            async with r['lock']:
                if r['sockets'][seat] is not ws:continue
                if action=='start' and seat==0 and not r['started'] and all(r['sockets']):
                    r['started']=True;advance(r)
                elif action=='bid' and r['started'] and not r['done'] and not r['finished'] and seat==r['turn']:
                    if r['deadline'] is not None and time.time()>=r['deadline']:
                        if r['price']==0:bid(r)
                        else:settle(r)
                    else:bid(r)
                elif action=='pass' and r['started'] and not r['done'] and seat==r['turn'] and r['price']>0:
                    settle(r)
                elif action=='replay' and r['finished'] and seat==0 and all(r['sockets']):
                    r['deck']=new_deck()
                    r['index']=0
                    r['budgets']=[20,20]
                    r['teams']=[[],[]]
                    r['turn']=0
                    r['price']=0
                    r['leader']=None
                    r['deadline']=None
                    r['done']=False
                    r['finished']=False
                    r['notice']='Nouvelle partie !'
                    advance(r)
                elif action=='next' and r['started'] and r['done'] and seat==0:
                    r['index']+=1;advance(r)
                await broadcast(r)
    except (WebSocketDisconnect,ValueError):pass
    finally:
        if r and seat is not None and r['sockets'][seat] is ws:
            async with r['lock']:
                r['sockets'][seat]=None
                if seat==0:
                    rooms.pop(r['code'],None);r['clocktask'].cancel()
                    for other in r['sockets']:
                        if other:
                            try:await other.send_json({'type':'error','message':'Le créateur a quitté le salon. Recharge la page pour rejouer.'})
                            except Exception:pass
                else:
                    r['notice']='Le joueur 2 s’est déconnecté';await broadcast(r)
