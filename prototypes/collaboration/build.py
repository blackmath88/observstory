#!/usr/bin/env python3
"""Issue #7, DEVELOP: three concepts, all fed by the real engine on the synthetic hackathon.

  python3 prototypes/collaboration/build.py
    checkin/index.html               Direction 1: capture -> proposed -> review -> confirm
    mission-timeline/index.html      Direction 2: NOW, gates, check-ins, commitment due times
    declared-vs-observed/index.html  Direction 3: reconciliation cues, both sides side by side
"""

from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "fixtures"))

import collab_lab  # noqa: E402
from observstory import config, coordination as co  # noqa: E402
from observstory.derive import derive, parse_time  # noqa: E402

MOMENTS = ["kickoff", "saturday-morning", "after-core-freeze", "feature-freeze"]
BASE_CSS = """:root{--bg:#f6f5f1;--surface:#fdfcfa;--ink:#1d1d1f;--ink2:#515154;--ink3:#8a8a8e;--hair:#e4e2dc;--hair2:#d6d4cd;
--accent:#b4530a;--accent-t:#fbefe4;--select:#0a66d6;--ok:#2f6b4f;--sans:-apple-system,BlinkMacSystemFont,"SF Pro Text",system-ui,sans-serif;
--mono:ui-monospace,"SF Mono",Menlo,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.45 var(--sans)}
main{max-width:1180px;margin:auto;padding:24px 20px 48px}h1{font-size:20px;margin:4px 0 2px}
.eyebrow{font:600 11px var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--ink3)}
.muted{color:var(--ink3)}code,.mono{font-family:var(--mono);font-size:11.5px}
.card{background:var(--surface);border:1px solid var(--hair);border-radius:10px;padding:12px 14px}
button,input,textarea{font:inherit;color:inherit}
.tag{font:10.5px var(--mono);border:1px solid var(--hair);border-radius:4px;padding:0 5px;color:var(--ink2)}
.tabs{display:flex;gap:4px;margin:14px 0}.tabs button{border:1px solid var(--hair2);background:var(--surface);border-radius:7px;padding:3px 10px;cursor:pointer}
.tabs button[aria-pressed=true]{background:var(--ink);color:var(--surface)}"""


def moment(name, data):
    obs = json.loads((ROOT / "fixtures/collab-lab" / f"{name}.json").read_text())
    now = parse_time(obs["fetched_at"])
    snap = derive(obs, config.normalise(collab_lab.CONFIG), now, coordination=co.as_of(data, now))
    return {"name": name, "note": obs["note"], "coordination": snap["coordination"],
            "work": {w["id"]: {"title": w["title"], "state": w["state"]} for w in snap["work_items"]}}


def page(title, body, data, script):
    raw = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{title}</title><style>{BASE_CSS}{body[0]}</style></head><body><main>{body[1]}</main>"
            f"<script type=application/json id=data>{raw}</script><script>{script}</script></body></html>")


# ---------------------------------------------------------------- Direction 1: check-in capture
CHECKIN = (""".grid{display:grid;grid-template-columns:1fr 1.3fr;gap:18px;margin-top:14px}
textarea{width:100%;height:330px;border:1px solid var(--hair2);border-radius:8px;padding:10px;font:12px/1.5 var(--mono);background:var(--surface)}
.rec{display:flex;gap:10px;align-items:center;margin:6px 0 10px}.rec button{border:1px solid var(--hair2);border-radius:7px;padding:3px 10px;background:var(--surface);cursor:pointer}
.rec .live{color:#b3261e;font-weight:600}.item{display:grid;grid-template-columns:18px 1fr;gap:8px;padding:8px 0;border-top:1px solid var(--hair)}
.item input[type=text]{border:1px solid transparent;border-radius:5px;padding:1px 4px;background:transparent;width:100%}
.item input[type=text]:hover,.item input[type=text]:focus{border-color:var(--hair2);background:var(--surface)}
.item .src{color:var(--ink3);font-size:11px}.item.dropped{opacity:.4}.item.declared .state{color:var(--ok)}
h3{margin:14px 0 2px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)}
.state{font:10.5px var(--mono);color:var(--accent)}.confirm{display:flex;gap:8px;align-items:center;margin-top:14px;flex-wrap:wrap}
.confirm input{border:1px solid var(--hair2);border-radius:7px;padding:4px 8px;width:140px}
.confirm button{border:0;border-radius:7px;padding:5px 12px;background:var(--ink);color:var(--surface);cursor:pointer}
pre{white-space:pre-wrap;background:var(--surface);border:1px solid var(--hair);border-radius:8px;padding:10px;font:11.5px/1.5 var(--mono)}""",
"""<span class=eyebrow>Observstory · collaboration · direction 1 (prototype)</span><h1>Check-in capture</h1>
<p class=muted>Notes (or, later, a transcript) → <b>proposed</b> items → you review and edit → a named person confirms → <b>declared</b> state in <code>.observstory/coordination.json</code>.
The proposals below were produced by the real extractor (<code>observstory checkin propose</code>). Nothing becomes project state without the confirm step.</p>
<div class=grid><section><div class=rec><button type=button id=rec>● Record</button><span id=recstate class=muted>Not recording. v1 takes typed notes; recording needs everyone's consent first.</span></div>
<textarea id=notes spellcheck=false></textarea></section>
<section class=card><div id=items></div><div class=confirm><label>Confirmed by <input id=by placeholder="your name"></label>
<button type=button id=go>Confirm kept items</button><span id=msg class=muted></span></div><div id=out></div></section></div>""",
r"""const D=JSON.parse(document.getElementById('data').textContent);document.getElementById('notes').value=D.notes;
const box=document.getElementById('items');const groups=[['gates','Gates'],['commitments','Commitments'],['decisions','Decisions']];
function row(x,k){const d=document.createElement('div');d.className='item';d.dataset.id=x.id;
 const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;cb.onchange=()=>d.classList.toggle('dropped',!cb.checked);
 const t=document.createElement('div');const main=document.createElement('input');main.type='text';main.value=k==='gates'?x.label:x.text;
 const meta=document.createElement('div');meta.className='src';
 meta.textContent=(k==='commitments'?('@'+(x.owner||'?')+(x.due?' · due '+x.due.slice(11,16):'')+(x.links.length?' · '+x.links.map(l=>l.ref).join(', '):'')):k==='gates'?(x.kind+' · '+x.at.slice(5,16).replace('T',' ')+(x.areas.length?' · '+x.areas.join(', '):'')):(x.areas.length?x.areas.join(', '):''));
 const st=document.createElement('div');st.className='state';st.textContent='proposed · line '+x.source.line+' · '+x.id;st.title=x.source.excerpt;
 t.append(main,meta,st);d.append(cb,t);return d}
for(const[k,l]of groups){const h=document.createElement('h3');h.textContent=l;box.append(h);D.proposed[k].forEach(x=>box.append(row(x,k)))}
if(D.questions.length){const h=document.createElement('h3');h.textContent='Open questions (kept on the session)';box.append(h);
 D.questions.forEach(q=>{const p=document.createElement('div');p.className='item';p.textContent='? '+q;box.append(p)})}
let rec=false;document.getElementById('rec').onclick=()=>{if(!rec&&!confirm('Has everyone present agreed to being recorded?'))return;rec=!rec;
 document.getElementById('rec').textContent=rec?'■ Stop':'● Record';const s=document.getElementById('recstate');
 s.className=rec?'live':'muted';s.textContent=rec?'Recording (prototype: nothing is captured)':'Stopped. In a later version the local transcript would appear in the notes box.'};
document.getElementById('go').onclick=()=>{const by=document.getElementById('by').value.trim();const msg=document.getElementById('msg');
 if(!by){msg.textContent='A person has to confirm. Enter a name.';return}
 const dropped=[...box.querySelectorAll('.item.dropped')].map(d=>d.dataset.id);
 box.querySelectorAll('.item[data-id]').forEach(d=>{if(!d.classList.contains('dropped')){d.classList.add('declared');const s=d.querySelector('.state');s.textContent='declared · confirmed by '+by}});
 msg.textContent='';const cmd='observstory checkin confirm '+D.session+' --by "'+by+'"'+(dropped.length?' --drop '+dropped.join(','):'');
 const o=document.getElementById('out');o.innerHTML='';const h=document.createElement('h3');h.textContent='What this does';
 const p=document.createElement('pre');p.textContent=cmd+'\n\n# then commit .observstory/coordination.json; the next Observstory run reconciles it with the repository';o.append(h,p)};""")

# ---------------------------------------------------------------- Direction 2: mission timeline
TIMELINE = (""".rail{position:relative;height:150px;margin:18px 10px 8px}.axis{position:absolute;left:0;right:0;top:70px;height:2px;background:var(--hair2)}
.past{position:absolute;left:0;top:70px;height:2px;background:var(--ink3)}.now{position:absolute;top:26px;height:92px;width:0;border-left:1.5px solid var(--ink)}
.now span{position:absolute;top:-18px;left:-14px;font:600 10.5px var(--mono)}.m{position:absolute;transform:translateX(-50%);text-align:center;font-size:11px;white-space:nowrap}
.gate{top:40px}.gate i{display:block;margin:0 auto 2px;width:2px;height:26px;background:var(--ink)}.gate.passed{color:var(--ink3)}.gate.passed i{background:var(--ink3)}
.gate.next b{color:var(--ink)}.gate.hot i{background:var(--accent)}.gate.hot{color:var(--accent)}
.ses{top:64px}.ses i{display:block;margin:0 auto;width:12px;height:12px;border-radius:50%;background:var(--surface);border:2px solid var(--ink2)}.ses span{display:block;margin-top:4px;color:var(--ink3)}
.due{top:98px}.due i{display:block;margin:0 auto;width:9px;height:9px;transform:rotate(45deg);background:var(--ink3)}
.due.in_progress i{background:var(--select)}.due.landed i{background:var(--ok)}.due.not_started i{background:transparent;border:1.5px solid var(--ink3)}.due.hot i{border-color:var(--accent)}
.due span{display:block;margin-top:4px;color:var(--ink3);font-size:10.5px}.head{display:flex;justify-content:space-between;align-items:baseline;gap:20px;flex-wrap:wrap}
.nextgate{font-size:15px}.nextgate b{font-weight:600}.list{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px;margin-top:10px}
.c{padding:8px 10px}.c .s{font:10.5px var(--mono);color:var(--ink3)}.c.hot{border-color:var(--accent)}""",
"""<span class=eyebrow>Observstory · collaboration · direction 2 (prototype)</span><h1>Mission timeline</h1>
<p class=muted>Declared gates and check-ins on one rail, with commitment due times below it. Observed state (linked work) colours the commitments. Orange marks a relation that needs a look.</p>
<div class=tabs id=tabs></div><section class=card><div class=head><div class=nextgate id=next></div><div class=muted id=note></div></div>
<div class=rail id=rail></div><div class=list id=list></div></section>""",
r"""const D=JSON.parse(document.getElementById('data').textContent);const T=s=>Date.parse(s);
function show(i){const M=D.moments[i],C=M.coordination;document.querySelectorAll('#tabs button').forEach((b,k)=>b.setAttribute('aria-pressed',k===i));
 const now=T(C.now),t0=T(D.start),t1=T(D.end),x=v=>(100*(v-t0)/(t1-t0)).toFixed(2)+'%';const hot=new Set(C.cues.map(q=>q.subject.id));
 const r=document.getElementById('rail');r.innerHTML='<div class=axis></div><div class=past style="width:'+x(now)+'"></div><div class=now style="left:'+x(now)+'"><span>NOW</span></div>';
 for(const s of C.sessions){r.insertAdjacentHTML('beforeend','<div class="m ses" style="left:'+x(T(s.at))+'"><i></i><span>'+s.label.replace(' check-in','')+'</span></div>')}
 for(const g of C.gates){const c=['m','gate',g.passed?'passed':'',g.next?'next':'',hot.has(g.id)?'hot':''].join(' ');
  r.insertAdjacentHTML('beforeend','<div class="'+c+'" style="left:'+x(T(g.at))+'"><b>'+g.label+'</b><i></i>'+g.at.slice(11,16)+'</div>')}
 for(const c of C.commitments){if(!c.due)continue;r.insertAdjacentHTML('beforeend','<div class="m due '+c.state+(c.cue?' hot':'')+'" style="left:'+x(T(c.due))+'"><i></i><span>'+c.id+'</span></div>')}
 const n=C.gates.find(g=>g.next);const h=n?Math.round((T(n.at)-now)/36e5*10)/10:null;
 document.getElementById('next').innerHTML=n?'Next: <b>'+n.label+'</b> at '+n.at.slice(11,16)+' · in '+h+' h':'All gates passed';
 document.getElementById('note').textContent=M.note;const L=document.getElementById('list');L.innerHTML='';
 for(const c of C.commitments){const w=c.matched.map(m=>(M.work[m]||{}).title?m.replace('pr:','#'):m).join(', ');
  L.insertAdjacentHTML('beforeend','<div class="card c'+(c.cue?' hot':'')+'"><div class=s>'+c.id+' · '+(c.owner||'')+' · due '+(c.due||'').slice(11,16)+'</div><div>'+c.text+'</div><div class=s>'+c.state.replace('_',' ')+(w?' · '+w:'')+'</div></div>')}}
const tabs=document.getElementById('tabs');D.moments.forEach((m,i)=>{const b=document.createElement('button');b.textContent=m.label;b.onclick=()=>show(i);tabs.append(b)});show(2);""")

# ---------------------------------------------------------------- Direction 3: declared vs observed
DVO = (""".cue{display:grid;grid-template-columns:1fr 150px 1fr;gap:0;margin:10px 0;padding:0}.cue>div{padding:12px 14px}
.side .k{font:600 10.5px var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);margin-bottom:4px}
.rel{display:flex;align-items:center;justify-content:center;text-align:center;color:var(--accent);font-size:11.5px;border-left:1px solid var(--hair);border-right:1px solid var(--hair);background:var(--accent-t)}
.obs{background:color-mix(in srgb,var(--ink) 2%,transparent)}.meta{color:var(--ink3);font-size:11.5px;margin-top:4px}
@media(max-width:760px){.cue{grid-template-columns:1fr}.rel{border:0;border-top:1px solid var(--hair);border-bottom:1px solid var(--hair);padding:6px}}""",
"""<span class=eyebrow>Observstory · collaboration · direction 3 (prototype)</span><h1>Declared vs observed</h1>
<p class=muted>Each cue puts what the team declared next to what the repository shows. The middle says how they relate, without judging anyone.</p>
<div class=tabs id=tabs></div><div id=cues></div>""",
r"""const D=JSON.parse(document.getElementById('data').textContent);const REL={'commitment.unstarted':'no linked work yet','freeze.changed_after':'changed after the freeze','gate.passed_with_open_work':'gate passed, work still open'};
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML}
function show(i){const M=D.moments[i],C=M.coordination;document.querySelectorAll('#tabs button').forEach((b,k)=>b.setAttribute('aria-pressed',k===i));
 const box=document.getElementById('cues');box.innerHTML=C.cues.length?'':'<p class=muted>No cues at this moment: declarations and the repository agree.</p>';
 for(const q of C.cues){const d=q.declared,o=q.observed;const sess=C.sessions.find(s=>s.id===d.session);
  box.insertAdjacentHTML('beforeend','<section class="card cue"><div class=side><div class=k>Declared</div><div>'+esc(d.text)+'</div><div class=meta>'+
  esc([d.owner?('owner '+d.owner):'',d.due?('due '+d.due.slice(11,16)):'',d.at?('at '+d.at.slice(11,16)):'',d.areas&&d.areas.length?d.areas.join(', '):''].filter(Boolean).join(' · '))+
  '</div><div class=meta>'+esc((sess?sess.label+' · ':'')+'confirmed by '+d.confirmed_by)+'</div></div><div class=rel>'+esc(REL[q.rule]||q.rule)+'<br>'+esc(q.confidence)+
  '</div><div class="side obs"><div class=k>Observed</div><div>'+esc(o.work_items.length?o.work_items.map(w=>w.startsWith('pr:')?'#'+w.slice(3)+' '+((M.work[w]||{}).title||''):w.startsWith('direct:')?'a direct push':w).join(' · '):'nothing linked')+
  '</div><div class=meta>'+esc(o.detail)+'</div></div></section>')}}
const tabs=document.getElementById('tabs');D.moments.forEach((m,i)=>{const b=document.createElement('button');b.textContent=m.label;b.onclick=()=>show(i);tabs.append(b)});show(2);""")


def main():
    full = collab_lab.declarations()
    labels = {"kickoff": "Fri 19:00 · kickoff", "saturday-morning": "Sat 09:30", "after-core-freeze": "Sat 15:00",
              "feature-freeze": "Sat 23:00"}
    moments = [dict(moment(m, full), label=labels[m]) for m in MOMENTS]

    draft = co.empty()
    sid = co.propose(draft, collab_lab.KICKOFF_NOTES, "Kickoff", "2026-10-02T18:30:00Z", kind="kickoff")
    checkin = {"notes": collab_lab.KICKOFF_NOTES, "session": sid,
               "proposed": {k: draft[k] for k in ("gates", "commitments", "decisions")},
               "questions": draft["sessions"][0]["open_questions"]}
    rail = {"start": "2026-10-02T17:00:00Z", "end": "2026-10-04T07:00:00Z", "moments": moments}
    for sub, title, spec, data in (("checkin", "Check-in capture", CHECKIN, checkin),
                                   ("mission-timeline", "Mission timeline", TIMELINE, rail),
                                   ("declared-vs-observed", "Declared vs observed", DVO, rail)):
        (HERE / sub).mkdir(exist_ok=True)
        (HERE / sub / "index.html").write_text(page(title, spec[:2], data, spec[2]), encoding="utf-8")
        print(f"{sub}/index.html")


if __name__ == "__main__":
    main()
