import os,sys,json,time,html,sqlite3,requests
from concurrent.futures import ThreadPoolExecutor,as_completed

try:
    from colorama import Fore,Style,init
    init(autoreset=True)
except ImportError:
    class _C:
        GREEN = RED = CYAN = YELLOW = RESET_ALL = BRIGHT = ''
    Fore = Style = _C()

# ═══════════════════════════════════════════════════════
#  🔐 CONFIG & TOKEN (Read from config file)
# ═══════════════════════════════════════════════════════
if not os.path.exists("config.txt"):
    print("❌ Config file nahi mili. Pehle run.py chalao.")
    sys.exit()

with open("config.txt", "r") as f:
    lines = f.read().splitlines()
    BOT_TOKEN = lines[0]
    ADMIN_ID = int(lines[1])

API=f"https://api.telegram.org/bot{BOT_TOKEN}"
ADMIN_HANDLE="@d9xac"
OWNER_NAME="HARSHU"
TEAM_NAME="Team Plugger"
BOT_TITLE="HI2 Mail Checker Bot"
WELCOME_BONUS=20
REFERRAL_BONUS=5
FORCE_JOIN_BONUS=20
BULK_LIMIT=30

# ═══════════════════════════════════════════════════════
#  👑 VIP IDs (Auto Unlimited)
# ═══════════════════════════════════════════════════════
VIP_IDS = [
    8954138750, 8944336986, 8931696518, 8883573151, 8874739824,
    8869639003, 8866765799, 8835844930, 8815528432, 8813178440,
    8804520327, 8759825097, 8746972448, 8649053494, 8621945493,
    8560319159, 8528881910, 8526844095, 8512786954, 8466741761,
    8461135003, 8352193392, 8240366776, 7970385221, 7898701659,
    7809093531, 7394255125, 6939318242, 6931549302
]

# ═══════════════════════════════════════════════════════
#  📢 FORCE CHANNELS
# ═══════════════════════════════════════════════════════
FORCE_CHANNELS=[
    {"name":"PLUGGER 0001","url":"https://t.me/plugger0001","id":"@plugger0001"},
    {"name":"PLUGGER 0002","url":"https://t.me/plugger0002","id":"@plugger0002"},
    {"name":"PLUGGER 0003","url":"https://t.me/plugger0003","id":"@plugger0003"},
    {"name":"TEAM PLUGGER","url":"https://t.me/plugger089","id":"@plugger089"},
    {"name":"A4A PLUGGER","url":"https://t.me/A4Aplugger","id":"@A4Aplugger"},
    {"name":"PLUGGER FILES","url":"https://t.me/pluggersfiles","id":"@pluggersfiles"},
]

DB="bot_database.db"
executor=ThreadPoolExecutor(max_workers=50)
processed=set()
modes={}
runtime={"welcome":WELCOME_BONUS,"referral":REFERRAL_BONUS,"bulk":BULK_LIMIT}
processed_clicks={}

def init_db():
    c=sqlite3.connect(DB,timeout=10).cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,credits INTEGER DEFAULT 0,is_unlimited INTEGER DEFAULT 0,is_blocked INTEGER DEFAULT 0,referred_by INTEGER DEFAULT 0,referral_count INTEGER DEFAULT 0,state TEXT DEFAULT '',join_bonus_given INTEGER DEFAULT 0)''')
    c.connection.commit();c.connection.close()
init_db()

def gu(uid):
    conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    c.execute("SELECT credits,is_unlimited,state,is_blocked,referred_by,referral_count,join_bonus_given FROM users WHERE user_id=?",(uid,))
    r=c.fetchone()
    if not r:
        c.execute("INSERT INTO users(user_id,credits,is_unlimited,state,is_blocked)VALUES(?,0,0,'',0)",(uid,));conn.commit()
        r=(0,0,'',0,0,0,0)
    conn.close()
    return {"credits":r[0] or 0,"unl":bool(r[1]),"state":r[2] or '','blocked':bool(r[3]),"refby":r[4] or 0,"refc":r[5] or 0,"jbg":r[6] or 0}

def uex(uid):
    conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    c.execute("SELECT 1 FROM users WHERE user_id=?",(uid,));r=c.fetchone();conn.close()
    return r is not None

def cnu(uid,ref=0):
    conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(user_id,credits,is_unlimited,state,is_blocked,referred_by)VALUES(?,?,0,'',0,?)",(uid,runtime["welcome"],ref))
    conn.commit();conn.close()

def sjbg(uid):
    conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    c.execute("UPDATE users SET join_bonus_given=1 WHERE user_id=?",(uid,));conn.commit();conn.close()

def sref(uid,ref):
    conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    c.execute("UPDATE users SET referred_by=? WHERE user_id=?",(ref,uid))
    c.execute("UPDATE users SET referral_count=referral_count+1 WHERE user_id=?",(ref,))
    conn.commit();conn.close()

def sus(uid,state):
    gu(uid);conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    c.execute("UPDATE users SET state=? WHERE user_id=?",(state,uid));conn.commit();conn.close()

def acred(uid,amt):
    gu(uid);conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    if amt==-1:c.execute("UPDATE users SET is_unlimited=1 WHERE user_id=?",(uid,))
    else:c.execute("UPDATE users SET credits=credits+? WHERE user_id=?",(amt,uid))
    conn.commit();conn.close()

def rcred(uid,amt):
    gu(uid);conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
    c.execute("UPDATE users SET credits=MAX(0,credits-?) WHERE user_id=?",(amt,uid));conn.commit();conn.close()

def dcred(uid,n):
    u=gu(uid)
    if u["unl"]:return True
    if u["credits"]>=n:
        conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
        c.execute("UPDATE users SET credits=credits-? WHERE user_id=?",(n,uid));conn.commit();conn.close();return True
    return False

def hdr():
    return f"╔═══════════════════════════════╗\n   ✦ <b><i>『 {TEAM_NAME} 』</i></b> ✦\n   <b><i>{BOT_TITLE} 😽</i></b>\n╚═══════════════════════════════╝\n"

def sm(chat,text,rm=None):
    d={"chat_id":chat,"text":text,"parse_mode":"HTML","disable_web_page_preview":True}
    if rm:d["reply_markup"]=json.dumps(rm)
    try:return requests.post(f"{API}/sendMessage",data=d,timeout=6).json().get("result",{}).get("message_id")
    except:return None

def em(chat,mid,text,rm=None):
    d={"chat_id":chat,"message_id":mid,"text":text,"parse_mode":"HTML","disable_web_page_preview":True}
    if rm:d["reply_markup"]=json.dumps(rm)
    try:return requests.post(f"{API}/editMessageText",data=d,timeout=6).json().get("ok")
    except:return False

def dm(chat,mid):
    try:requests.post(f"{API}/deleteMessage",data={"chat_id":chat,"message_id":mid},timeout=3)
    except:pass

def acq(cqid,text=None):
    d={"callback_query_id":cqid}
    if text:d["text"]=text
    try:requests.post(f"{API}/answerCallbackQuery",data=d,timeout=3)
    except:pass

def gbu():
    try:return requests.get(f"{API}/getMe",timeout=5).json().get("result",{}).get("username","")
    except:return ""

def gup(off=None):
    try:return requests.get(f"{API}/getUpdates",params={"timeout":1,"offset":off},timeout=4).json().get("result",[])
    except:return []

def clr():
    try:requests.get(f"{API}/deleteWebhook?drop_pending_updates=True",timeout=5)
    except:pass

_join_cache={}
_join_lock=__import__("threading").Lock()

def _check_one(uid,ch,retries=2):
    for attempt in range(retries+1):
        try:
            r=requests.get(f"{API}/getChatMember",params={"chat_id":ch["id"],"user_id":uid},timeout=8).json()
            if r.get("ok"):
                status=r.get("result",{}).get("status","")
                return status not in("left","kicked")
            else:
                time.sleep(0.3)
        except Exception:
            if attempt==retries:return None
            time.sleep(0.4)
    return None

def chk_join(uid,use_cache=False):
    now=time.time()
    if use_cache:
        with _join_lock:
            if uid in _join_cache:
                ts,ok,missing=_join_cache[uid]
                if now-ts<5:return ok,missing
    results={}
    with ThreadPoolExecutor(max_workers=len(FORCE_CHANNELS) or 1) as ex:
        futures={ex.submit(_check_one,uid,ch):ch for ch in FORCE_CHANNELS}
        for fut in as_completed(futures,timeout=20):
            ch=futures[fut]
            try:results[ch["id"]]=fut.result()
            except Exception:results[ch["id"]]=None
    missing=[ch for ch in FORCE_CHANNELS if results.get(ch["id"]) is not True]
    all_joined=(len(missing)==0)
    with _join_lock:
        _join_cache[uid]=(now,all_joined,missing)
    return all_joined,missing

def send_fj(chat,mid=None,nj=None):
    if nj is None:nj=FORCE_CHANNELS
    L=["╔═══════════════════════════════╗","   ⚠️ <b>𝗝𝗢𝗜𝗡 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗</b> ⚠️","╚═══════════════════════════════╝","",f"🔒 <b>Bot use karne ke liye saare {len(nj)} channels join karo!</b>","","━━━━━━━━━━━━━━━━━━━━━━━"]
    for i,ch in enumerate(nj,1):L.append(f"  {i}. <b>{html.escape(ch['name'])}</b>")
    L+=["━━━━━━━━━━━━━━━━━━━━━━━","",f"🎁 <b>Saare join karne par {FORCE_JOIN_BONUS} CREDITS FREE!</b>","","👇 <b>Neeche button dabao:</b>","Join ke baad <b>✅ I HAVE JOINED</b> dabao"]
    kb=[[{"text":f"📢 JOIN {ch['name']}","url":ch["url"]}] for ch in nj]
    kb.append([{"text":"✅ I HAVE JOINED ALL","callback_data":"check_join"}])
    if mid:dm(chat,mid)
    sm(chat,"\n".join(L),{"inline_keyboard":kb})

def req_join(chat,mid=None,fn="User"):
    joined,nj=chk_join(chat)
    if joined:
        u=gu(chat)
        if not u.get("jbg"):
            acred(chat,FORCE_JOIN_BONUS)
            sjbg(chat)
            sm(chat,f"🎉 <b>SAARE CHANNELS JOINED!</b>\n\n🎁 +<b>{FORCE_JOIN_BONUS} FREE CREDITS</b>!\n✨ Ab bot use kar sakte ho!")
        return True
    send_fj(chat,mid,nj)
    return False

def solve_rc():
    try:
        s=requests.Session()
        anchor="https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfEUPkgAAAAAKTgbMoewQkWBEQhO2VPL4QviKct&co=aHR0cHM6Ly9oaTIuaW46NDQz&hl=en&v=XrIDux0s7SoNe6_IHkjGC92W&size=invisible"
        p=anchor.split('?')[1]
        h={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        r=s.get(f'https://www.google.com/recaptcha/enterprise/anchor?{p}',headers=h,timeout=5)
        if 'recaptcha-token" value="' not in r.text:return None
        tok=r.text.split('recaptcha-token" value="')[1].split('"')[0]
        v=p.split('v=')[1].split('&')[0]
        pl=f"v={v}&reason=q&c={tok}&k=6LfEUPkgAAAAAKTgbMoewQkWBEQhO2VPL4QviKct&co=aHR0cHM6Ly9oaTIuaW46NDQz&hl=en&size=invisible"
        hr={"User-Agent":h["User-Agent"],"Referer":f"https://www.google.com/recaptcha/enterprise/anchor?{p}","Content-Type":"application/x-www-form-urlencoded"}
        r2=s.post('https://www.google.com/recaptcha/enterprise/reload',data=pl,headers=hr,timeout=5)
        if 'resp","' in r2.text:return r2.text.split('resp","')[1].split('"')[0]
    except:pass
    return None

def chk_hi2(email):
    if "@" in email:prefix,domain=email.split("@",1)
    else:prefix,domain=email,"hi2.in"
    sol=solve_rc()
    if not sol:return None
    d={'domain':domain,'prefix':prefix,'recaptcha':sol}
    h={'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",'Accept':"application/json, text/plain, */*",'authorization':"Basic bnVsbA==",'Origin':"https://hi2.in",'Referer':"https://hi2.in/"}
    try:
        r=requests.post("https://hi2.in/api/custom",data=d,headers=h,timeout=6)
        t=r.text.lower()
        if "already taken" in t or "taken" in t:return False
        elif "success" in t or "created" in t or r.status_code==200:return True
    except:pass
    return None

def hi2_status(email):
    r=None
    for _ in range(2):
        r=chk_hi2(email)
        if r is not None:break
        time.sleep(0.3)
    if r is True:return "🟢 <b>Available</b>"
    if r is False:return "🔴 <b>Taken</b>"
    return "⚠️ <b>Error/Timeout</b>"

def welcome(chat,fn="User",mid=None):
    u=gu(chat)
    if not fn or fn.strip()=="" or fn=="User": fn="User"
    sn=html.escape(str(fn))
    if u["blocked"]:
        if mid:dm(chat,mid)
        sm(chat,"<b>🚫 YOU ARE BLOCKED BY ADMIN.</b>");return
    if u["unl"]:plan="👑 <b>Unlimited Plan</b>";cr="♾️ <b>UNLIMITED</b>"
    elif u["credits"]>0:plan="💎 <b>Active Credits Plan</b>";cr=f"⚡ <b>{u['credits']}</b>"
    else:plan="❌ <b>No Active Plan</b>";cr="<b>0</b>"
    cap=(f"{hdr()}\n┏━━━━━━━━━━━━━━━━━━━━━━━┓\n   ✨ <b>ʜᴇʏ {sn}</b> ✨\n┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
         f"👤 <b>𝗡𝗮𝗺𝗲 :</b> <b>{sn}</b>\n🆔 <b>𝗜𝗗 :</b> <code>{chat}</code>\n"
         f"📜 <b>𝗣𝗹𝗮𝗻 :</b> {plan}\n⚡ <b>𝗖𝗿𝗲𝗱𝗶𝘁𝘀 :</b> {cr}\n"
         f"🎁 <b>𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹𝘀 :</b> <b>{u['refc']}</b>\n\n"
         f"╭─────────────────────╮\n   🛡 <b>𝗔𝗱𝗺𝗶𝗻 :</b> <code>{ADMIN_HANDLE}</code>\n   👑 <b>𝗢𝘄𝗻𝗲𝗿 :</b> <b>{OWNER_NAME}</b>\n╰─────────────────────╯\n\n"
         f"━━━━━━━━━━━━━━━━━━━━━━━\n🎯 <b>Select an option below to start</b>\n━━━━━━━━━━━━━━━━━━━━━━━")
    kb=[[{"text":"⚡️ 𝐒𝐈𝐍𝐆𝐋𝐄 𝐌𝐎𝐃𝐄","callback_data":"m_single"},{"text":"🚀 𝐁𝐔𝐋𝐊 𝐌𝐎𝐃𝐄","callback_data":"m_bulk"}]]
    if u["unl"]:kb.append([{"text":"📊 𝐌𝐘 𝐒𝐓𝐀𝐓𝐔𝐒","callback_data":"v_stat"},{"text":"🎁 𝐑𝐄𝐅𝐄𝐑𝐀𝐋","callback_data":"ref"}])
    else:
        kb.append([{"text":"💎 𝐁𝐔𝐘 𝐂𝐑𝐄𝐃𝐈𝐓𝐒","callback_data":"plans"},{"text":"📊 𝐌𝐘 𝐒𝐓𝐀𝐓𝐔𝐒","callback_data":"v_stat"}])
        kb.append([{"text":"🎁 𝐑𝐄𝐅𝐄𝐑 𝐀𝐍𝐃 𝐄𝐀𝐑𝐍","callback_data":"ref"}])
    if mid:dm(chat,mid)
    sm(chat,cap,{"inline_keyboard":kb})

def status(chat,fn="User",mid=None):
    u=gu(chat);sn=html.escape(str(fn))
    if u["unl"]:plan="👑 <b>Unlimited</b>";cr="♾️ <b>UNLIMITED</b>"
    elif u["credits"]>0:plan="💎 <b>Credits Plan</b>";cr=f"⚡ <b>{u['credits']}</b>"
    else:plan="❌ <b>No Plan</b>";cr="<b>0</b>"
    msg=(f"╔═══════════════════════════╗\n  📊 𝗬𝗢𝗨𝗥 𝗦𝗧𝗔𝗧𝗨𝗦 📊\n╚═══════════════════════════╝\n\n"
         f"👤 <b>𝗡𝗮𝗺𝗲 :</b> <b>{sn}</b>\n🆔 <b>𝗜𝗗 :</b> <code>{chat}</code>\n"
         f"📜 <b>𝗣𝗹𝗮𝗻 :</b> {plan}\n⚡ <b>𝗖𝗿𝗲𝗱𝗶𝘁𝘀 :</b> {cr}\n"
         f"🎁 <b>𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹𝘀 :</b> <b>{u['refc']}</b>\n\n"
         f"🛡 <b>Admin :</b> <code>{ADMIN_HANDLE}</code>\n👑 <b>Owner :</b> <b>{OWNER_NAME}</b>")
    kb=[]
    if not u["unl"]:kb.append([{"text":"💎 BUY CREDITS","callback_data":"plans"}])
    kb.append([{"text":"🔙 MAIN MENU","callback_data":"back"}])
    if mid:dm(chat,mid)
    sm(chat,msg,{"inline_keyboard":kb})

def referral(chat,mid=None):
    u=gu(chat);bu=gbu();link=f"https://t.me/{bu}?start=REF{chat}"
    msg=(f"╔═══════════════════════════╗\n   🎁 𝗥𝗘𝗙𝗘𝗥 & 𝗘𝗔𝗥𝗡 🎁\n╚═══════════════════════════╝\n\n"
         f"💎 <b>Invite friends & earn FREE credits!</b>\n\n"
         f"🎯 <b>Reward :</b> <b>+{runtime['referral']} Credits</b>\n"
         f"👥 <b>Total Referrals :</b> <b>{u['refc']}</b>\n\n"
         f"🔗 <b>YOUR LINK</b>\n\n<code>{link}</code>\n\n"
         f"📤 <b>Share karo aur paisa kamao!</b>\n🛡 <b>Admin :</b> <code>{ADMIN_HANDLE}</code>")
    kb={"inline_keyboard":[[{"text":"📤 SHARE LINK","url":f"https://t.me/share/url?url={link}&text=Join this bot!"}],[{"text":"🔙 MAIN MENU","callback_data":"back"}]]}
    if mid:dm(chat,mid)
    sm(chat,msg,kb)

def do_single(chat,u):
    usr=gu(chat)
    if usr["blocked"]:return
    if not usr["unl"] and usr["credits"]<1:plans(chat);return
    mid=sm(chat,"⚡ <b>Checking... Please wait</b> ⏳")
    u=u.strip().lower()
    ems=[u] if "@" in u else [f"{u}@hi2.in",f"{u}@telegmail.com"]
    if not dcred(chat,len(ems)):
        em(chat,mid,"❌ <b>INSUFFICIENT CREDITS!</b>");plans(chat);return
    with ThreadPoolExecutor(max_workers=2) as ex:
        res=list(ex.map(lambda e:f"📧 <code>{e}</code> ➜ {hi2_status(e)}",ems))
    fin="━━━━━━━━━━━━━━━━━━━━━━━\n"+"\n".join(res)+"\n━━━━━━━━━━━━━━━━━━━━━━━"
    em(chat,mid,fin) if mid else sm(chat,fin)

def do_bulk(chat,text):
    raw=text.strip().split()
    ems=[e.strip().lower() for e in raw if e.strip() and "@" in e]
    if not ems:sm(chat,"❌ <b>No valid emails.</b>");return
    tot=len(ems)
    if tot>runtime["bulk"]:
        first=ems[:runtime["bulk"]];rest=ems[runtime["bulk"]:]
        conn=sqlite3.connect(DB,timeout=10);c=conn.cursor()
        c.execute("UPDATE users SET state=? WHERE user_id=?",(json.dumps(rest),chat))
        conn.commit();conn.close()
    else:
        first=ems;rest=[]
    usr=gu(chat)
    if usr["blocked"]:return
    if not usr["unl"] and usr["credits"]<len(first):
        sm(chat,f"❌ <b>INSUFFICIENT CREDITS!</b>\n⚡ You have {usr['credits']} but need {len(first)}")
        plans(chat);return
    wait_time=len(first)+5
    mid=sm(chat,f"⏳ <b>Checking {len(first)} emails...</b>\n<i>Please wait ~{wait_time} seconds</i>")
    if not dcred(chat,len(first)):
        em(chat,mid,"❌ <b>Deduct error!</b>");return
    rd={}
    for i,e in enumerate(first):
        if i%5==0:
            em(chat,mid,f"⏳ <b>Checking {i+1}/{len(first)} emails...</b>\n<i>Please wait...</i>")
        rd[e]=hi2_status(e)
        time.sleep(1)
    res=[f"📧 <code>{e}</code> ➜ {rd[e]}" for e in first if e in rd]
    fin="━━━━━━━━━━━━━━━━━━━━━━━\n"+"\n".join(res)+"\n━━━━━━━━━━━━━━━━━━━━━━━"
    em(chat,mid,fin) if mid else sm(chat,fin)
    if rest:
        kb={"inline_keyboard":[[{"text":"✅ YES","callback_data":"pending_yes"},{"text":"❌ NO","callback_data":"pending_no"}]]}
        sm(chat,f"⚠️ <b>{len(rest)} mail pending.</b>\nDo you want to check them?",kb)

def auto_add_vip():
    print(Fore.CYAN + "[*] Adding VIP IDs to Unlimited..." + Style.RESET_ALL)
    for uid in VIP_IDS:
        try:
            acred(uid, -1)
            print(f"  [+] ID {uid} -> UNLIMITED")
        except: pass

def handle(upd):
    if "callback_query" in upd:
        cq=upd["callback_query"];cid=cq["id"]
        now=time.time()
        if cid in processed_clicks and now-processed_clicks[cid]<2:return
        processed_clicks[cid]=now
        acq(cid)
        msg_obj = cq.get("message", {})
        chat_type = msg_obj.get("chat", {}).get("type", "")
        
        if chat_type != "private":
            return
            
        chat = msg_obj.get("chat", {}).get("id")
        mid = msg_obj.get("message_id")
        if not chat:return
        d=cq.get("data","");fu=cq.get("from",{});fn=fu.get("first_name","User")

        if d=="pending_yes":
            u=gu(chat)
            try:
                rest=json.loads(u["state"]);sus(chat,"");dm(chat,mid)
                executor.submit(do_bulk,chat," ".join(rest))
            except:sm(chat,"❌ Error processing pending mails.")
            return
        if d=="pending_no":
            sus(chat,"");dm(chat,mid);sm(chat,"✅ Pending mails cancelled.");return

        if d=="check_join":
            u=gu(chat);j,nj=chk_join(chat,use_cache=False)
            if j:
                if not u["jbg"]:acred(chat,FORCE_JOIN_BONUS);sjbg(chat);sm(chat,f"🎉 <b>JOINED!</b>\n\n🎁 +<b>{FORCE_JOIN_BONUS} CREDITS</b>!")
                welcome(chat,fn,mid)
            else:send_fj(chat,mid,nj)
            return
        if d=="v_stat":
            if req_join(chat,mid,fn):status(chat,fn,mid)
            return
        if d=="ref":
            if req_join(chat,mid,fn):referral(chat,mid)
            return
        if d=="m_single":
            if not req_join(chat,mid,fn):return
            u=gu(chat)
            if not u["unl"] and u["credits"]<1:plans(chat,mid)
            else:modes[chat]="single";dm(chat,mid);sm(chat,"📩 <b>Send mail</b> 👇🏻")
            return
        if d=="m_bulk":
            if not req_join(chat,mid,fn):return
            u=gu(chat)
            if not u["unl"] and u["credits"]<1:plans(chat,mid)
            else:modes[chat]="bulk";dm(chat,mid);sm(chat,f"📩 <b>Send mails line by line</b>\n\n⚠️ Max {runtime['bulk']} per batch")
            return
        if d=="back":modes[chat]=None;welcome(chat,fn,mid);return
        return

    if "message" in upd:
        m=upd["message"]
        chat_type=m.get("chat",{}).get("type","")
        
        if chat_type != "private":
            return
            
        chat=m["chat"]["id"];t=m.get("text","");fu=m.get("from",{});fn=fu.get("first_name","User")
        if t and t.startswith("/start"):
            p=t.split();rid=0
            if len(p)>1 and p[1].startswith("REF"):
                try:rid=int(p[1].replace("REF",""))
                except:rid=0
            isnew=not uex(chat);modes[chat]=None
            if isnew:
                ar=0
                if rid and rid!=chat and uex(rid):ar=rid
                cnu(chat,ar)
                sm(chat,f"🎉 <b>WELCOME!</b>\n\n🎁 +<b>{runtime['welcome']} FREE CREDITS</b>")
                if ar:
                    acred(ar,runtime["referral"]);sref(chat,ar)
                    try:sm(ar,f"🎁 <b>REFERRAL!</b>\n\n👤 {html.escape(fn)} joined!\n⚡ +{runtime['referral']} Credits")
                    except:pass
            if not req_join(chat,fn=fn):return
            welcome(chat,fn);return
        if t=="/help":
            modes[chat]=None
            if not req_join(chat,fn=fn):return
            welcome(chat,fn);return
        u=gu(chat)
        if t and not t.startswith("/"):
            if not req_join(chat,fn=fn):return
            cm=modes.get(chat)
            if cm is None:welcome(chat,fn)
            elif cm=="single":executor.submit(do_single,chat,t)
            elif cm=="bulk":executor.submit(do_bulk,chat,t)

def run():
    clr()
    print(Fore.GREEN+"╔═══━━━───〔 ✦ 〕───━━━═══╗\n║  TEAM PLUGGER BOT v24    ║\n║  HI2 + USER PANEL        ║\n╚═══━━━───〔 ✦ 〕───━━━═══╝"+Style.RESET_ALL)
    
    auto_add_vip()
    print(Fore.CYAN+"✅ Saari Unlimited IDs add ho gayi hain!"+Style.RESET_ALL)

    last=0
    while True:
        try:
            ups=gup(last+1)
            for u in ups:
                uid=u.get("update_id")
                if not uid or uid in processed:continue
                processed.add(uid)
                if len(processed)>5000:processed.clear()
                if uid>=last:last=uid
                executor.submit(handle,u)
            time.sleep(0.01)
        except KeyboardInterrupt:print(f"\n{Fore.RED}Stopped{Style.RESET_ALL}");break
        except Exception as e:print(f"{Fore.RED}Err: {e}{Style.RESET_ALL}");time.sleep(1)

if __name__=="__main__":
    try:
        os.system('clear' if os.name!='nt' else 'cls')
    except Exception:
        pass
    run()