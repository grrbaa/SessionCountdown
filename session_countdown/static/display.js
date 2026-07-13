const el=id=>document.getElementById(id); let state={sessions:[]};
function fmt(ms){ if(ms<=0) return '00:00:00'; const s=Math.floor(ms/1000),h=Math.floor(s/3600),m=Math.floor((s%3600)/60); return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`; }
function tick(){
 const now=new Date(); el('clock').textContent=now.toLocaleString([], {weekday:'short',hour:'2-digit',minute:'2-digit',second:'2-digit'}); el('event').textContent=state.event_name||'Race Event'; el('circuit').textContent=state.circuit||''; el('message').textContent=state.message||'';
 const sessions=(state.sessions||[]).map(s=>({...s,startDate:new Date(s.start)})).sort((a,b)=>a.startDate-b.startDate); const next=sessions.find(s=>s.startDate>now);
 if(!next){ el('label').textContent='SCHEDULE COMPLETE'; el('name').textContent=sessions.length?'No more sessions':'No timetable loaded'; el('countdown').textContent='--:--:--'; el('ground').textContent=''; return; }
 el('label').textContent='NEXT SESSION'; el('name').textContent=next.name; el('countdown').textContent=fmt(next.startDate-now); el('ground').textContent=next.ground_by?`Car on ground: ${new Date(next.ground_by).toLocaleString()}`:`Starts: ${next.startDate.toLocaleString()}`;
}
const ws=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws`); ws.onopen=()=>el('connection').textContent='Connected'; ws.onclose=()=>el('connection').textContent='Offline — using last timetable'; ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.type==='timetable')state=m.payload}; fetch('/api/timetable').then(r=>r.json()).then(x=>state=x); setInterval(tick,250); tick();
