const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
$("#menuBtn").onclick=()=>$("#nav").classList.toggle("open");
$("#accountBtn").onclick=()=>$("#accountModal").classList.add("open");
$("#closeAccount").onclick=()=>$("#accountModal").classList.remove("open");
$("#accountModal").onclick=e=>{if(e.target===$("#accountModal"))$("#accountModal").classList.remove("open")};
$$(".accountOption").forEach(b=>b.onclick=()=>alert("EM CONSTRUÇÃO — nenhum dado foi enviado."));
$("#helpBtn").onclick=()=>$("#help").scrollIntoView({behavior:"smooth"});

const guided=$("#guided"), steps=[$("#step1"),$("#step2"),$("#step3")];
let selectedArea="", guidedOriginal="";
const hints={
creator:"Conte qual rede social, assunto e duração aproximada.",
sales:"Conte qual produto você quer divulgar e onde pretende publicar.",
education:"Conte a matéria, tema e nível de estudo.",
voice:"Cole ou descreva o texto que você quer transformar em narração.",
music:"Conte o estilo, tema e clima da música.",
work:"Conte se precisa de e-mail, currículo, relatório, divulgação ou outra tarefa."
};
const paths={
creator:"1. Definir objetivo e público\n2. Montar roteiro\n3. Criar cenas\n4. Preparar título, descrição, CTA e hashtags",
sales:"1. Preservar o produto original\n2. Definir plataforma e público\n3. Criar gancho e roteiro UGC\n4. Preparar CTA, descrição e cenas",
education:"1. Identificar matéria e nível\n2. Explicar o assunto com clareza\n3. Organizar resumo/atividade\n4. Revisar o aprendizado",
voice:"1. Revisar o texto\n2. Abrir Estúdio de Voz\n3. Escolher uma voz do aparelho\n4. Ouvir e ajustar velocidade/tom",
music:"1. Definir estilo e tema\n2. Organizar estrutura e refrão\n3. Preparar letra/ideia\n4. Geração de áudio real continuará EM CONSTRUÇÃO",
work:"1. Identificar a tarefa\n2. Organizar informações essenciais\n3. Montar documento/texto\n4. Revisar antes de usar"
};
function showStep(n){steps.forEach((s,i)=>s.classList.toggle("hidden",i!==n-1));$("#stepLabel").textContent=`Passo ${n} de 3`}
$("#guideStart").onclick=()=>{guided.classList.remove("hidden");showStep(1);guided.scrollIntoView({behavior:"smooth"})};
$("#quickStart").onclick=()=>$("#promptStudio").scrollIntoView({behavior:"smooth"});
$$("[data-area]").forEach(b=>b.onclick=()=>{selectedArea=b.dataset.area;$("#areaHint").textContent=hints[selectedArea];showStep(2)});
$("#back1").onclick=()=>showStep(1);
$("#buildPath").onclick=()=>{guidedOriginal=$("#guidedText").value.trim();if(!guidedOriginal)return alert("Conte em poucas palavras o que você precisa.");$("#pathResult").textContent=paths[selectedArea]+"\n\nSeu pedido: "+guidedOriginal;showStep(3)};
$("#restart").onclick=()=>{$("#guidedText").value="";showStep(1)};
$("#sendPrompt").onclick=()=>{$("#prompt").value=guidedOriginal;$("#promptStudio").scrollIntoView({behavior:"smooth"})};

$$(".format").forEach(b=>b.onclick=()=>{$$(".format").forEach(x=>x.classList.remove("active"));b.classList.add("active")});
$$(".tool").forEach(b=>b.onclick=()=>{$$(".tool").forEach(x=>x.classList.remove("active"));b.classList.add("active")});
$("#demoBtn").onclick=()=>{let t=$("#prompt").value.trim(),tool=$(".tool.active")?.dataset.tool||"Prompt",fmt=$(".format.active")?.textContent||"9:16";$("#demoOut").classList.remove("hidden");$("#demoOut").textContent=t?`${tool} • ${fmt}\n\nObjetivo: ${t}\n\n1. Gancho/abertura clara\n2. Desenvolvimento organizado\n3. Fechamento com CTA\n\nDemonstração local — 0 créditos.`:"Escreva primeiro o que você quer criar."};

$$("[data-target]").forEach(c=>c.onclick=()=>$("#"+c.dataset.target).scrollIntoView({behavior:"smooth"}));

const vt=$("#voiceText"), count=$("#count"), dur=$("#duration"), sel=$("#voiceSelect");let voices=[];
vt.oninput=()=>{let n=vt.value.length;count.textContent=n;dur.textContent="~"+(n?Math.max(1,Math.round(n/900)):0)+" min"};
function loadVoices(){voices=speechSynthesis.getVoices();sel.innerHTML="";voices.forEach((v,i)=>{let o=document.createElement("option");o.value=i;o.textContent=`${v.name} — ${v.lang}`;sel.appendChild(o)})}
speechSynthesis.onvoiceschanged=loadVoices;loadVoices();
$("#speak").onclick=()=>{if(!vt.value.trim())return alert("Digite ou cole uma narração.");speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(vt.value);u.voice=voices[+sel.value]||null;u.rate=+$("#rate").value;u.pitch=+$("#pitch").value;speechSynthesis.speak(u)};
$("#pause").onclick=()=>speechSynthesis.paused?speechSynthesis.resume():speechSynthesis.pause();
$("#stop").onclick=()=>speechSynthesis.cancel();

const help={"Como começar":"Toque em “Não sei por onde começar”. A V6 conduz você em 3 passos.","Créditos":"Os 20 créditos são somente demonstração visual. Não existe cobrança nesta V6.","Voz":"O Estúdio de Voz usa as vozes disponíveis no seu aparelho, sem API paga.","Criar conteúdo":"Use o ChatCreova Guiado ou vá direto ao Prompt Studio.","Conta e cadastro":"A interface já existe, mas login e cadastro reais continuam EM CONSTRUÇÃO.","Pagamentos":"Nenhum pagamento está conectado nesta versão."};
$$(".helpChoice").forEach(b=>b.onclick=()=>$("#helpOut").textContent=help[b.textContent]||"");
$$(".music button").forEach(b=>b.onclick=()=>{$("#prompt").value=`Quero planejar uma música no estilo ${b.textContent}. `;$("#promptStudio").scrollIntoView({behavior:"smooth"})});
// ===== V7: Equipe AI + Meu Espaço + Internacional =====
const $v7 = (id) => document.getElementById(id);
function v7Scroll(id){ const el=$v7(id); if(el) el.scrollIntoView({behavior:"smooth",block:"start"}); }

$v7("doWithMe")?.addEventListener("click",()=>v7Scroll("teamAI"));

$v7("runBoss")?.addEventListener("click",()=>{
  const task=$v7("bossTask").value.trim();
  if(!task){ alert("Conte ao Encarregado o que você quer produzir."); return; }
  const lower=task.toLowerCase();
  const agents=["🧠 Encarregado AI","✍️ Roteirista AI","📱 Social Media AI"];
  if(/imagem|capa|foto|design|thumb/.test(lower)) agents.push("🎨 Designer AI — geração: EM CONSTRUÇÃO");
  if(/vídeo|video|reel|short|tiktok|kwai/.test(lower)) agents.push("🎬 Editor AI — geração/montagem automática: EM CONSTRUÇÃO");
  if(/voz|narra|locução|locucao|áudio|audio/.test(lower)) agents.push("🎙️ Locutor AI");
  if(/traduz|inglês|ingles|espanhol|francês|frances|alemão|alemao|japonês|japones|chinês|chines|internacional/.test(lower)) agents.push("🌍 Tradutor AI — tradução automática: EM CONSTRUÇÃO");
  if(/música|musica|trilha|jingle/.test(lower)) agents.push("🎵 Produtor Musical AI");
  const result=$v7("bossResult");
  result.classList.remove("hidden");
  result.innerHTML=`<b>Ordem recebida.</b><p>${task.replace(/</g,"&lt;")}</p><p><b>Equipe escalada:</b><br>${agents.join("<br>")}</p><p><b>Plano:</b> objetivo → roteiro → materiais → voz/áudio → montagem → conteúdo para publicação.</p><small>V7 local: o plano é real; recursos dependentes de API continuam identificados como EM CONSTRUÇÃO.</small>`;
});

const STORE_KEY="chatcreova_v7_channels";
function loadChannels(){
  try{return JSON.parse(localStorage.getItem(STORE_KEY)||"[]")}catch(e){return[]}
}
function renderChannels(){
  const box=$v7("channelList"); if(!box) return;
  const items=loadChannels();
  if(!items.length){box.innerHTML='<p class="muted">Nenhum canal/projeto salvo neste aparelho.</p>';return}
  box.innerHTML=items.map((x,i)=>`<div class="savedItem">
    <b>${escapeHtml(x.name)}</b> • ${escapeHtml(x.platform)}
    <p>${escapeHtml(x.niche||"Sem nicho")} | ${escapeHtml(x.country||"Mercado não informado")} | ${escapeHtml(x.language)}</p>
    <p>${escapeHtml(x.audience||"Público não informado")}</p>
    ${x.memory?`<p><b>Memória:</b> ${escapeHtml(x.memory)}</p>`:""}
    <div class="savedActions"><button onclick="useChannel(${i})">Usar no Prompt Studio</button><button onclick="deleteChannel(${i})">Excluir</button></div>
  </div>`).join("");
}
function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
window.deleteChannel=function(i){const a=loadChannels();a.splice(i,1);localStorage.setItem(STORE_KEY,JSON.stringify(a));renderChannels()}
window.useChannel=function(i){
  const x=loadChannels()[i]; if(!x)return;
  const p=$v7("promptInput")||document.querySelector("#promptStudio textarea");
  if(p){p.value=`Criar para o projeto "${x.name}" (${x.platform}). Nicho: ${x.niche}. Mercado: ${x.country}. Idioma: ${x.language}. Público: ${x.audience}. Regras/memória: ${x.memory}. `;v7Scroll("promptStudio");p.focus();}
}
$v7("saveChannel")?.addEventListener("click",()=>{
  const name=$v7("channelName").value.trim();
  if(!name){alert("Digite o nome do canal ou projeto.");return}
  const a=loadChannels();
  a.push({name,platform:$v7("channelPlatform").value,niche:$v7("channelNiche").value.trim(),country:$v7("channelCountry").value.trim(),language:$v7("channelLanguage").value,audience:$v7("channelAudience").value.trim(),memory:$v7("channelMemory").value.trim()});
  localStorage.setItem(STORE_KEY,JSON.stringify(a));renderChannels();
  $v7("channelName").value=""; $v7("channelNiche").value=""; $v7("channelCountry").value=""; $v7("channelAudience").value=""; $v7("channelMemory").value="";
});
renderChannels();

$v7("intlPrepare")?.addEventListener("click",()=>{
  const text=$v7("intlText").value.trim(); if(!text){alert("Digite ou cole o conteúdo.");return}
  const lang=$v7("intlLanguage").selectedOptions[0].text;
  const market=$v7("intlMarket").value.trim()||"mercado a definir";
  const p=$v7("promptInput")||document.querySelector("#promptStudio textarea");
  if(p){p.value=`Preparar este conteúdo para ${market}, idioma ${lang}. Adaptar linguagem, referências e formato ao público-alvo sem inventar fatos. Conteúdo: ${text}`;v7Scroll("promptStudio");p.focus();}
});

// Filter browser voices by the selected international language when possible.
const voiceLangSelect=document.createElement("select");
voiceLangSelect.id="voiceLanguageV7";
voiceLangSelect.innerHTML='<option value="">🌐 Todas as vozes</option><option value="pt">Português</option><option value="en">English</option><option value="es">Español</option><option value="fr">Français</option><option value="de">Deutsch</option><option value="ja">日本語</option><option value="zh">中文</option>';
const voicePanel=$v7("voiceStudio");
if(voicePanel){
  const firstSelect=voicePanel.querySelector("select");
  if(firstSelect) firstSelect.parentNode.insertBefore(voiceLangSelect,firstSelect);
}

voiceLangSelect?.addEventListener("change",()=>{
  const sel=document.querySelector("#voiceStudio select:not(#voiceLanguageV7)");
  if(!sel || !window.speechSynthesis) return;
  const lang=voiceLangSelect.value;
  const voices=speechSynthesis.getVoices().filter(v=>!lang||v.lang.toLowerCase().startsWith(lang));
  if(voices.length){
    sel.innerHTML=voices.map((v,i)=>`<option value="${i}">${escapeHtml(v.name)} — ${escapeHtml(v.lang)}</option>`).join("");
  }
});

// ===== V8: dois modos + Gerente Geral conversacional + biblioteca gratuita =====
document.getElementById("managerMode")?.addEventListener("click",()=>document.getElementById("teamAI")?.scrollIntoView({behavior:"smooth"}));
document.getElementById("manualMode")?.addEventListener("click",()=>document.getElementById("promptStudio")?.scrollIntoView({behavior:"smooth"}));

document.querySelectorAll(".templateBtn").forEach(btn=>{
  btn.addEventListener("click",()=>{
    const t=document.getElementById("bossTask");
    if(t){t.value=btn.dataset.template||"";document.getElementById("teamAI")?.scrollIntoView({behavior:"smooth"});t.focus();}
  });
});

// Voice-to-text for the Gerente, when supported by the browser/device.
const SpeechRecognitionV8 = window.SpeechRecognition || window.webkitSpeechRecognition;
document.getElementById("managerMic")?.addEventListener("click",()=>{
  const status=document.getElementById("micStatus");
  if(!SpeechRecognitionV8){ if(status) status.textContent="Reconhecimento de voz não disponível neste navegador."; return; }
  const rec=new SpeechRecognitionV8();
  rec.lang="pt-BR"; rec.interimResults=false; rec.maxAlternatives=1;
  if(status) status.textContent="🎤 Ouvindo...";
  rec.onresult=e=>{const t=document.getElementById("bossTask");if(t)t.value=e.results[0][0].transcript;if(status)status.textContent="Pedido recebido. Revise e envie ao Gerente.";};
  rec.onerror=()=>{if(status)status.textContent="Não consegui ouvir. Você pode digitar o pedido.";};
  rec.onend=()=>{if(status && status.textContent==="🎤 Ouvindo...")status.textContent="Digite ou fale seu pedido";};
  rec.start();
});

// Upgrade the local manager response into an organized step-by-step intake.
const oldBoss=document.getElementById("runBoss");
if(oldBoss){
  const replacement=oldBoss.cloneNode(true);
  oldBoss.parentNode.replaceChild(replacement,oldBoss);
  replacement.addEventListener("click",()=>{
    const input=document.getElementById("bossTask");
    const task=(input?.value||"").trim();
    if(!task){alert("Explique ao Gerente o que você precisa.");return;}
    const low=task.toLowerCase();
    let area="Projeto geral";
    let questions=[];
    let steps=["Entender o objetivo","Organizar o projeto","Preparar os materiais","Revisar o resultado"];
    if(/vender|produto|shopee|tiktok|loja|anúncio|anuncio/.test(low)){
      area="Vendas & E-commerce"; questions=["Qual é o produto?","Em qual plataforma será usado?","Qual duração/formato você quer?"];
      steps=["Definir produto e plataforma","Criar gancho e roteiro","Organizar cenas e prompts","Preparar narração/CTA","Preparar título, descrição e hashtags"];
    } else if(/aplicativo|app|site|empresa|sistema/.test(low)){
      area="Sites, Apps & Empresas"; questions=["O que sua empresa faz?","Quem vai usar?","Quais funções são indispensáveis?"];
      steps=["Levantar requisitos","Definir páginas e fluxo","Planejar identidade e dados","Estruturar desenvolvimento","Planejar testes e implantação"];
    } else if(/história|historia|escola|trabalho|estudar|professor|aluno/.test(low)){
      area="Educação"; questions=["Qual é o nível de ensino?","Qual formato do trabalho?","Existe tamanho ou prazo definido?"];
      steps=["Definir tema e nível","Organizar tópicos","Explicar passo a passo","Revisar clareza","Preparar apresentação/atividade se necessário"];
    } else if(/vídeo|video|reel|short|cinematográfico|cinematografico/.test(low)){
      area="Vídeo & Conteúdo"; questions=["Qual plataforma?","Qual duração?","Qual estilo e público?"];
      steps=["Definir objetivo","Criar roteiro","Planejar cenas/prompts","Preparar voz e trilha","Orientar montagem e publicação"];
    }
    const result=document.getElementById("bossResult");
    if(result){
      result.classList.remove("hidden");
      result.innerHTML=`<b>🧠 Gerente Geral — ${area}</b><p><b>Seu pedido:</b> ${escapeHtml(task)}</p>
      <p><b>Plano inicial:</b><br>${steps.map((s,i)=>`${i+1}. ${escapeHtml(s)}`).join("<br>")}</p>
      <p><b>Para deixar o projeto certo, confirme quando necessário:</b><br>${questions.map(q=>"• "+escapeHtml(q)).join("<br>")||"• O pedido já contém informações suficientes para começar."}</p>
      <small>V8 Beta local: o Gerente organiza e orienta. Recursos que dependem de APIs externas continuam desligados ou EM CONSTRUÇÃO.</small>`;
    }
  });
}
