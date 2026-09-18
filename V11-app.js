const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
const sidebar=$("#sidebar"), input=$("#mainInput"), chat=$("#chat");
const STORE="chatcreovaV11State", PROJECTS="chatcreovaV11Projects";
let state=JSON.parse(localStorage.getItem(STORE)||"null")||{brief:{},stage:0,lastRequest:"",deliveries:[]};
function persist(){localStorage.setItem(STORE,JSON.stringify(state))}
function openView(id){$$('.view').forEach(v=>v.classList.toggle('active',v.id===id));$$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===id));if(innerWidth<801)sidebar.classList.remove('open')}
$$('.nav').forEach(b=>b.onclick=()=>openView(b.dataset.view));
$('#menuBtn').onclick=()=>sidebar.classList.toggle('open');
function toast(msg){let d=document.createElement('div');d.className='toast';d.textContent=msg;document.body.appendChild(d);setTimeout(()=>d.remove(),2600)}
$$('[data-open]').forEach(b=>b.onclick=()=>openView(b.dataset.open));
$$('[data-fill]').forEach(b=>b.onclick=()=>{input.value=b.dataset.fill;openView('manager');input.focus()});
$$('[data-manager]').forEach(b=>b.onclick=()=>{input.value=b.dataset.manager;openView('manager');input.focus()});
$$('.toolgrid article').forEach(card=>{if(card.querySelector('mark')?.textContent.includes('EM CONSTRUÇÃO')&&!card.dataset.manager&&!card.dataset.open){card.style.cursor='pointer';card.onclick=()=>toast('Em construção — nenhum crédito será cobrado.')}});
function addMsg(kind,html){const d=document.createElement('div');d.className='msg '+kind;d.innerHTML=html;chat.appendChild(d);d.scrollIntoView({behavior:'smooth',block:'end'})}
function clean(s){return s.replace(/[<>]/g,'')}
function parseBrief(text){const t=text.toLowerCase(), b=state.brief;
 if(/facebook/.test(t))b.platform='Facebook'; if(/instagram/.test(t))b.platform='Instagram'; if(/tiktok/.test(t))b.platform='TikTok'; if(/kwai/.test(t))b.platform='Kwai';
 let d=t.match(/(\d+)\s*(segundos?|s|minutos?|min)/); if(d)b.duration=d[1]+' '+(d[2].startsWith('m')?'minutos':'segundos');
 if(/salmo\s*91/.test(t))b.theme='Salmo 91'; else if(/supera[cç][aã]o/.test(t))b.theme='história emocionante de superação';
 if(/cinematogr/.test(t))b.style='cinematográfico'; if(/produto|vender|e-commerce|ecommerce/.test(t))b.type='vendas'; else if(/vídeo|video|reel|short/.test(t))b.type='vídeo';
 if(/imagem|foto|capa/.test(t)&&!b.type)b.type='imagem'; if(/narra|voz|locu/.test(t)&&!b.type)b.type='voz';
 if(/\b(\d+)\s*cenas?/.test(t))b.scenes=+(t.match(/\b(\d+)\s*cenas?/)[1]);
 if(/roteiro/.test(t))b.script=true; if(/narra/.test(t))b.narration=true; if(/prompts?/.test(t))b.prompts=true; if(/hashtags?/.test(t))b.hashtags=true; if(/descri[cç][aã]o/.test(t))b.description=true; if(/\bcta\b/.test(t))b.cta=true;
 persist(); return b;
}
function teamFor(b){let a=['🧠 Gerente Geral'];if(b.type==='vídeo'||b.platform)a.push('✍️ Roteirista AI','🎬 Editor AI','📱 Social Media AI');if(b.narration||b.type==='voz')a.push('🎙️ Locutor AI');if(b.prompts||b.type==='imagem')a.push('🎨 Designer AI');return [...new Set(a)]}
function summary(b){let a=[];if(b.type)a.push('tipo: '+b.type);if(b.platform)a.push('plataforma: '+b.platform);if(b.duration)a.push('duração: '+b.duration);if(b.theme)a.push('tema: '+b.theme);if(b.scenes)a.push('cenas: '+b.scenes);return a.join(' • ')}
function isContinue(t){return /^(sim|s|ok|pode|pode continuar|continua|continuar|vai|prossiga|segue|faça|faca)$/i.test(t.trim())||/pode continuar|continue|próxima etapa|proxima etapa/i.test(t)}
function makeDelivery(b,stage){const theme=b.theme||'o tema solicitado', platform=b.platform||'redes sociais', dur=b.duration||'formato curto', n=b.scenes||8;
 if(stage===1)return `<b>🧠 Gerente Geral — Organização concluída</b><p><b>Projeto:</b> ${theme}<br><b>Destino:</b> ${platform} • ${dur}<br><b>Estrutura:</b> gancho forte → desenvolvimento → virada emocional → fechamento/CTA.</p><p>Já guardei essas informações. Vou avançar sem perguntar novamente o que você já informou.</p>`;
 if(stage===2){let scenes=Array.from({length:n},(_,i)=>`${i+1}. ${i===0?'Gancho visual imediato':i===n-1?'Fechamento emocional + CTA':'Cena de progressão '+i}`).join('<br>');return `<b>🧠 Gerente Geral — Produção</b><p><b>Roteiro-base (${dur}):</b><br>“Há momentos em que tudo parece difícil. Mas cada passo, mesmo pequeno, pode mudar o rumo de uma história. ${theme==='Salmo 91'?'O Salmo 91 lembra proteção, confiança e esperança mesmo em tempos de medo.':'A superação começa quando a pessoa decide continuar, mesmo sem enxergar todo o caminho.'} O que parecia fim pode se tornar recomeço. Continue avançando.”</p><p><b>${n} cenas planejadas:</b><br>${scenes}</p>`}
 if(stage===3)return `<b>🧠 Gerente Geral — Revisão</b><p><b>Prompt visual-base:</b> cena cinematográfica realista, iluminação dramática, emoção clara, composição vertical ou adaptada para ${platform}, alta definição, sem texto embutido.</p><p><b>Título:</b> Uma História Que Pode Mudar Seu Dia<br><b>Descrição:</b> Uma mensagem curta sobre ${theme}, feita para inspirar e gerar reflexão.<br><b>CTA:</b> Comente o que mais falou com você e compartilhe com alguém que precisa desta mensagem.<br><b>Hashtags:</b> #Superação #Motivação #Esperança #Inspiração #${platform.replace(/\s/g,'')}</p>`;
 return `<b>🧠 Gerente Geral — Projeto pronto</b><p>O pacote local foi organizado com roteiro, cenas, direção visual e publicação. Gerações externas continuam desligadas; esta etapa não consumiu créditos.</p>`;
}
function updateProgress(stage){const p=$('#progress');p.classList.remove('hidden');let spans=p.querySelectorAll('span');spans.forEach((s,i)=>{s.classList.remove('on','done','current');if(i<stage)s.classList.add('done');else if(i===Math.min(stage,spans.length-1))s.classList.add('current')})}
function respond(text){let continuation=isContinue(text);if(!continuation){parseBrief(text);state.lastRequest=text;state.stage=1}else{state.stage=Math.min(4,Math.max(1,state.stage+1))}persist();let b=state.brief;$('#team').classList.remove('hidden');$('#team').innerHTML='<b>Equipe selecionada:</b> '+teamFor(b).join(' • ');updateProgress(state.stage);return makeDelivery(b,state.stage)}
function send(){const text=input.value.trim();if(!text)return;openView('manager');addMsg('user',`<b>Você</b><p>${clean(text)}</p>`);input.value='';setTimeout(()=>addMsg('ai',respond(text)),180)}
$('#sendBtn').onclick=send;input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
// Anexo local real: escolhe arquivo e mostra nome/tamanho; não envia para API.
const filePicker=document.createElement('input');filePicker.type='file';filePicker.hidden=true;filePicker.multiple=true;document.body.appendChild(filePicker);
$('#attachBtn').onclick=()=>filePicker.click();filePicker.onchange=()=>{let files=[...filePicker.files];if(!files.length)return;openView('manager');addMsg('ai',`<b>📎 Anexo local</b><p>${files.map(f=>clean(f.name)+' — '+Math.ceil(f.size/1024)+' KB').join('<br>')}</p><p>Arquivo selecionado localmente. Nenhuma API paga foi usada.</p>`)};
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;$('#micBtn').onclick=()=>{if(!SR){toast('Reconhecimento de fala não está disponível neste navegador.');return}let r=new SR();r.lang='pt-BR';r.onresult=e=>{input.value=e.results[0][0].transcript;input.focus()};r.start()};
$('#helpBtn').onclick=()=>$('#helpModal').classList.remove('hidden');$('#closeHelp').onclick=()=>$('#helpModal').classList.add('hidden');
const vt=$('#voiceText'),vc=$('#voiceSelect');function voices(){let vs=speechSynthesis.getVoices();vc.innerHTML=vs.map((v,i)=>`<option value="${i}">${v.name} — ${v.lang}</option>`).join('')}voices();speechSynthesis.onvoiceschanged=voices;
vt.oninput=()=>{$('#count').textContent=vt.value.length;$('#duration').textContent='~'+Math.max(0,Math.round(vt.value.trim().split(/\s+/).filter(Boolean).length/150))+' min'};
$('#speak').onclick=()=>{speechSynthesis.cancel();if(!vt.value.trim())return toast('Digite ou cole uma narração primeiro.');let u=new SpeechSynthesisUtterance(vt.value),vs=speechSynthesis.getVoices();if(vs[+vc.value])u.voice=vs[+vc.value];u.lang=u.voice?.lang||'pt-BR';speechSynthesis.speak(u)};$('#pause').onclick=()=>speechSynthesis.paused?speechSynthesis.resume():speechSynthesis.pause();$('#stop').onclick=()=>speechSynthesis.cancel();
function renderProjects(){let a=JSON.parse(localStorage.getItem(PROJECTS)||'[]');$('#savedProjects').innerHTML=a.map(x=>`<article class="msg ai"><b>${clean(x.name)}</b><p>${clean(x.notes)}</p></article>`).join('')}
$('#saveProject').onclick=()=>{let name=$('#projectName').value.trim(),notes=$('#projectNotes').value.trim();if(!name)return toast('Digite o nome do projeto.');let a=JSON.parse(localStorage.getItem(PROJECTS)||'[]');a.unshift({name,notes});localStorage.setItem(PROJECTS,JSON.stringify(a.slice(0,30)));renderProjects();toast('Projeto salvo neste navegador.')};renderProjects();
