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