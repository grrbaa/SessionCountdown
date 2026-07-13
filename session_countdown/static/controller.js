const el = id => document.getElementById(id);
let state = {event_name:'Race Event',circuit:'',message:'',sessions:[]};
function localDateValue(value){ if(!value) return ''; const d=new Date(value); const offset=d.getTimezoneOffset(); return new Date(d.getTime()-offset*60000).toISOString().slice(0,16); }
function iso(value){ return value ? new Date(value).toISOString() : null; }
function row(session={}){
  const wrap=document.createElement('div'); wrap.className='session'; wrap.dataset.id=session.id||crypto.randomUUID();
  wrap.innerHTML=`<label>Name<input class="name" value="${session.name||''}"></label><label>Start<input class="start" type="datetime-local" value="${localDateValue(session.start)}"></label><label>Car on ground<input class="ground" type="datetime-local" value="${localDateValue(session.ground_by)}"></label><button class="secondary remove">Remove</button>`;
  wrap.querySelector('.remove').onclick=()=>wrap.remove(); return wrap;
}
function render(data){ state=data; el('eventName').value=data.event_name||''; el('circuit').value=data.circuit||''; el('message').value=data.message||''; el('sessions').replaceChildren(...data.sessions.map(row)); }
async function load(){ const r=await fetch('/api/timetable'); if(!r.ok) throw new Error('load failed'); render(await r.json()); }
async function save(){
  const sessions=[...document.querySelectorAll('.session')].map(r=>({id:r.dataset.id,name:r.querySelector('.name').value.trim(),start:iso(r.querySelector('.start').value),ground_by:iso(r.querySelector('.ground').value),end:null})).filter(s=>s.name&&s.start);
  const payload={event_name:el('eventName').value.trim()||'Race Event',circuit:el('circuit').value.trim(),message:el('message').value.trim(),sessions};
  const r=await fetch('/api/timetable',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(!r.ok){ alert(`Save failed: ${await r.text()}`); return; } render(await r.json()); el('status').textContent='Saved';
}
el('add').onclick=()=>el('sessions').append(row({name:'New session'})); el('save').onclick=save; el('openDisplay').onclick=()=>window.open('/display','_blank');
const ws=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws`); ws.onopen=()=>el('status').textContent='Pi connected'; ws.onclose=()=>el('status').textContent='Disconnected'; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.type==='timetable') render(m.payload)};
load().catch(()=>el('status').textContent='Connection error');
