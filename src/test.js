const fs=require('fs');const t=fs.readFileSync('template.html','utf8');eval(t.split('/*CORE*/')[1].split('/*END*/')[0]);
const D=JSON.parse(fs.readFileSync('data.json','utf8'));const nv=D.companies.find(c=>c.t==='NVDA').w;const cnt={};let sc=[];
for(const c of D.companies){const e=evaluate(c,D.fx,null,null,false);
 if(c.scout){if(e.sig==='pitch')sc.push(c.t+' '+e.m.toFixed(1)+'x');continue;}
 cnt[e.sig]=(cnt[e.sig]||0)+1;
 console.log(c.t.padEnd(5),e.sig.padEnd(6),e.sized?('z'+e.zone+' gap '+String(Math.round(e.gap*100)).padStart(4)+'%  base '+(e.R.base*100).toFixed(0).padStart(4)+'% bear '+(e.R.bear*100).toFixed(0).padStart(4)+'% (g '+(e.R.gB*100).toFixed(0)+'/'+(e.R.gR*100).toFixed(0)+') bearBE $'+Math.round(e.R.tR)+' top $'+Math.round(e.priceAt(c.top))):'unsized',' h'+e.h,' beta',(beta(c.w,nv)||0).toFixed(2),' 1y',((c.price/c.w[0]-1)*100).toFixed(0)+'%');}
console.log(cnt,'scout hits',sc.length,sc.join(', '));
