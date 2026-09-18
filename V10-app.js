const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
const sidebar=$("#sidebar"), input=$("#mainInput"), chat=$("#chat");
function openView(id){$$(".view").forEach(v=>v.classList.toggle("active",v.id===id));$$(".nav").forEach(n=>n.classList.toggle("active",n.dataset.view===id));if(innerWidth<801)sidebar.classList.remove("open");}
$$(".nav").forEach(b=>b.onclick=()=>openView(b.dataset.view));
$("#menuBtn").onclick=()=>sidebar.classList.toggle("open");
$$("[data-fill]").forEach(b=>b.onclick=()=>{input.value=b.dataset.fill;openView("manager");input.focus()});
function addMsg(kind,html){const d=document.createElement("div");d.className="msg "+kind;d.innerHTML=html;chat.appendChild(d);d.scrollIntoView({behavior:"smooth",block:"end"});}
function infer(text){
 const t=text.toLowerCase(); let team=["🧠 Gerente Geral"];
 if(/vídeo|reel|short|facebook|instagram|tiktok|kwai/.test(t)) team.push("✍️ Roteirista AI","📱 Social Media AI","🎬 Editor AI");
 if(/narra|voz|locu/.test(t)) team.push("🎙️ Locutor AI");
 if(/imagem|foto|capa|design/.test(t)) team.push("🎨 Designer AI");
 if(/música|trilha|samba|funk|gospel|sertanejo/.test(t)) team.push("🎵 Produtor Musical AI");
 if(/traduz|inglês|espanhol|internacional/.test(t)) team.push("🌍 Tradutor AI");
 let known=[];
 if(/facebook/.test(t)) known.push("plataforma: Facebook");
 if(/instagram/.test(t)) known.push("plataforma: Instagram");
 if(/tiktok/.test(t)) known.push("plataforma: TikTok");
 let dur=t.match(/(\d+)\s*(segundos?|s|minutos?|min)/); if(dur)known.push("duração: "+dur[0]);
 let plan = `<b>🧠 Gerente Geral</b><p>Pedido entendido${known.length?": "+known.join(" • "):""}.</p>
 <p><b>Vou organizar assim:</b><br>1. Definir o resultado e formato<br>2. Preparar o conteúdo principal<br>3. Separar cenas/prompts e materiais<br>4. Preparar publicação e revisão</p>
 <p>Nesta V10 local eu consigo organizar e manter a conversa. Gerações externas continuam desligadas até termos infraestrutura segura.</p>`;
 return {plan,team:[...new Set(team)]};
}
function send(){
 const text=input.value.trim(); if(!text)return;
 openView("manager"); addMsg("user",`<b>Você</b><p>${text.replace(/[<>]/g,"")}</p>`); input.value="";
 $("#progress").classList.remove("hidden");
 setTimeout(()=>{let r=infer(text);addMsg("ai",r.plan);$("#team").classList.remove("hidden");$("#team").innerHTML="<b>Equipe selecionada:</b> "+r.team.join(" • ");},250);
}
$("#sendBtn").onclick=send; input.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send()}});
$("#attachBtn").onclick=()=>addMsg("ai","<b>📎 Anexos</b><p>Estrutura preparada. Upload integrado será ativado em uma etapa futura.</p>");
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
$("#micBtn").onclick=()=>{if(!SR){addMsg("ai","<b>🎤 Voz</b><p>Reconhecimento de fala não está disponível neste navegador.</p>");return}let r=new SR();r.lang="pt-BR";r.onresult=e=>{input.value=e.results[0][0].transcript;input.focus()};r.start()};
$("#helpBtn").onclick=()=>$("#helpModal").classList.remove("hidden");$("#closeHelp").onclick=()=>$("#helpModal").classList.add("hidden");
const vt=$("#voiceText"), vc=$("#voiceSelect"); function voices(){let vs=speechSynthesis.getVoices();vc.innerHTML=vs.map((v,i)=>`<option value="${i}">${v.name} — ${v.lang}</option>`).join("")}voices();speechSynthesis.onvoiceschanged=voices;
vt.oninput=()=>{$("#count").textContent=vt.value.length;$("#duration").textContent="~"+Math.max(0,Math.round(vt.value.trim().split(/\s+/).length/150))+" min"};
$("#speak").onclick=()=>{speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(vt.value);let vs=speechSynthesis.getVoices();if(vs[+vc.value])u.voice=vs[+vc.value];u.lang=u.voice?.lang||"pt-BR";speechSynthesis.speak(u)};
$("#pause").onclick=()=>speechSynthesis.paused?speechSynthesis.resume():speechSynthesis.pause();$("#stop").onclick=()=>speechSynthesis.cancel();
function renderProjects(){let a=JSON.parse(localStorage.getItem("chatcreovaV10Projects")||"[]");$("#savedProjects").innerHTML=a.map((x,i)=>`<article class="msg ai"><b>${x.name}</b><p>${x.notes}</p></article>`).join("")}
$("#saveProject").onclick=()=>{let name=$("#projectName").value.trim(),notes=$("#projectNotes").value.trim();if(!name)return;let a=JSON.parse(localStorage.getItem("chatcreovaV10Projects")||"[]");a.unshift({name,notes});localStorage.setItem("chatcreovaV10Projects",JSON.stringify(a.slice(0,30)));renderProjects()};renderProjects();
