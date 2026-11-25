// Prints the scout queue: companies that clear both automatic passes and still need research.
// Run from the repo root: node src/scout.js
const fs=require('fs');const t=fs.readFileSync('src/template.html','utf8');eval(t.split('/*CORE*/')[1].split('/*END*/')[0]);
const D=JSON.parse(fs.readFileSync('docs/data.json','utf8'));
for(const c of D.companies){if(!c.scout)continue;const e=evaluate(c,D.fx,null,null,false),s=scoutScreen(c,e);
  if(s.clear)console.log('READY',c.t,c.name,(c.rs&&c.rs.verdict)?'researched: '+c.rs.verdict:'NEEDS RESEARCH',s.cyc?'(cyclical)':'');
  else if(s.pass1)console.log('stopped',c.t,s.fails.map(f=>f.id).join('+'));}
