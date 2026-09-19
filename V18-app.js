(()=>{
"use strict";

const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];

const OLLAMA="http://127.0.0.1:11434";
const MODEL="qwen3.5:0.8b";
const KEY="chatcreova_v18_channels";

const input=$("#input");
const messages=$("#messages");
const send=$("#send");
const status=$("#aiStatus");
const help=$("#help");

const history=[
  {
    role:"system",
    content:
      "Você é o ChatCreova AI, assistente oficial da plataforma ChatCreova. "+
      "Responda em português do Brasil por padrão, salvo pedido em outro idioma. "+
      "Converse naturalmente e execute o pedido do usuário. "+
      "Entregue conteúdo útil, completo e direto, sem placeholders. "+
      "Não exponha raciocínio interno. "+
      "Se perguntarem pelo motor, explique com transparência que nesta versão local "+
      "o ChatCreova utiliza um modelo Qwen executado pelo Ollama."
  }
];

function setStatus(text,state=""){
  if(!status)return;
  status.textContent=text;
  status.dataset.state=state;
}

function view(id){
  $$(".view").forEach(v=>{
    v.classList.toggle("active",v.id===id);
  });

  window.scrollTo({
    top:0,
    behavior:"smooth"
  });
}

function createMessage(role,text){
  const div=document.createElement("div");
  div.className="msg "+role;

  const title=document.createElement("b");
  title.textContent=
    role==="user"
      ?"Você"
      :"✦ ChatCreova AI";

  const p=document.createElement("p");
  p.textContent=text;

  div.append(title,p);
  messages.append(div);

  messages.scrollTop=messages.scrollHeight;

  return p;
}

function getChannels(){
  try{
    return JSON.parse(
      localStorage.getItem(KEY)||"[]"
    );
  }catch{
    return [];
  }
}

function setChannels(items){
  localStorage.setItem(
    KEY,
    JSON.stringify(items)
  );
}

function renderChannels(){

  const items=getChannels();
  const select=$("#channelSelect");
  const cards=$("#channelCards");

  if(!select||!cards)return;

  select.innerHTML=
    '<option value="">Sem canal/marca selecionado</option>';

  cards.innerHTML="";

  items.forEach((c,i)=>{

    const option=document.createElement("option");

    option.value=i;
    option.textContent=c.name;

    select.append(option);

    const card=document.createElement("div");

    card.className="channel-card";

    const title=document.createElement("strong");
    title.textContent=c.name;

    const info=document.createElement("p");

    info.textContent=[
      c.platform,
      c.niche,
      c.language
    ]
    .filter(Boolean)
    .join(" • ");

    card.append(title,info);
    cards.append(card);
  });
}

function channelContext(){

  const select=$("#channelSelect");

  if(!select||select.value==="")
    return "";

  const channel=
    getChannels()[Number(select.value)];

  if(!channel)
    return "";

  return (
    "\n\nContexto do canal ou marca:"+
    "\nNome: "+(channel.name||"")+
    "\nPlataforma: "+(channel.platform||"")+
    "\nNicho: "+(channel.niche||"")+
    "\nIdioma: "+(channel.language||"")+
    "\nRegras: "+(channel.rules||"")
  );
}

async function timed(
  url,
  options={},
  timeout=180000
){
  const controller=new AbortController();

  const timer=setTimeout(
    ()=>controller.abort(),
    timeout
  );

  try{
    return await fetch(
      url,
      {
        ...options,
        signal:controller.signal
      }
    );
  }
  finally{
    clearTimeout(timer);
  }
}

async function ollamaChat(chatMessages){

  const response=await timed(
    OLLAMA+"/api/chat",
    {
      method:"POST",

      headers:{
        "Content-Type":"application/json"
      },

      body:JSON.stringify({
        model:MODEL,
        messages:chatMessages,
        stream:false,
        think:false,
        keep_alive:"20m",
        options:{
          num_predict:900
        }
      })
    }
  );

  if(!response.ok)
    throw new Error(
      "HTTP "+response.status
    );

  const data=await response.json();

  let text=
    data?.message?.content?.trim()||"";

  text=text
    .replace(
      /<think>[\s\S]*?<\/think>/gi,
      ""
    )
    .trim();

  if(!text)
    throw new Error(
      "Resposta vazia"
    );

  return text;
}

async function checkAI(){

  setStatus(
    "Verificando IA...",
    "checking"
  );

  try{

    const response=await timed(
      OLLAMA+"/api/tags",
      {
        cache:"no-store"
      },
      10000
    );

    if(!response.ok)
      throw new Error(
        "HTTP "+response.status
      );

    const data=await response.json();

    const found=
      Array.isArray(data.models)&&
      data.models.some(
        m=>
          m.name===MODEL||
          m.model===MODEL
      );

    if(found){

      setStatus(
        "IA conectada",
        "connected"
      );

      return true;
    }

    setStatus(
      "Modelo não encontrado",
      "error"
    );

    return false;
  }
  catch(error){

    console.error(error);

    setStatus(
      "IA desconectada",
      "error"
    );

    return false;
  }
}

function errorMessage(error){

  if(error?.name==="AbortError")
    return "A IA demorou demais para responder.";

  if(error instanceof TypeError)
    return (
      "Não foi possível acessar a IA local. "+
      "Verifique se o Ollama está aberto neste computador."
    );

  return (
    "Falha na IA: "+
    (error?.message||"erro desconhecido.")
  );
}

async function sendMessage(){

  const text=input.value.trim();

  if(
    !text||
    send.disabled
  )return;

  createMessage(
    "user",
    text
  );

  input.value="";

  const waiting=
    createMessage(
      "ai",
      "Criando..."
    );

  history.push({
    role:"user",
    content:
      text+
      channelContext()
  });

  send.disabled=true;
  input.disabled=true;

  try{

    const answer=
      await ollamaChat(history);

    waiting.textContent=answer;

    history.push({
      role:"assistant",
      content:answer
    });

    setStatus(
      "IA conectada",
      "connected"
    );
  }
  catch(error){

    console.error(error);

    waiting.textContent=
      errorMessage(error);

    history.pop();

    setStatus(
      "IA desconectada",
      "error"
    );
  }
  finally{

    send.disabled=false;
    input.disabled=false;
    input.focus();
  }
}

async function runGenerator(
  button,
  prompt,
  resultSelector
){

  const result=$(resultSelector);

  if(!result)return;

  if(!prompt.trim()){

    result.textContent=
      "Preencha as informações antes de criar.";

    result.classList.add("show");

    return;
  }

  button.disabled=true;

  result.textContent=
    "✦ ChatCreova está criando...";

  result.classList.add("show");

  try{

    const answer=
      await ollamaChat([
        {
          role:"system",
          content:
            "Você é o ChatCreova AI. "+
            "Execute a tarefa solicitada em português do Brasil. "+
            "Entregue um resultado pronto para uso, organizado e direto. "+
            "Não exponha raciocínio interno."
        },
        {
          role:"user",
          content:
            prompt+
            channelContext()
        }
      ]);

    result.textContent=answer;

    setStatus(
      "IA conectada",
      "connected"
    );
  }
  catch(error){

    console.error(error);

    result.textContent=
      errorMessage(error);

    setStatus(
      "IA desconectada",
      "error"
    );
  }
  finally{

    button.disabled=false;
  }
}

function generatorPrompt(type){

  if(type==="video"){

    const idea=
      $("#videoIdea").value.trim();

    const format=
      $("#videoFormat").value;

    const duration=
      $("#videoDuration").value;

    return {
      prompt:
        "Crie um roteiro profissional de vídeo."+
        "\nTema: "+idea+
        "\nFormato: "+format+
        "\nDuração: "+duration+
        "\nInclua gancho inicial, cenas, narração ou falas, "+
        "orientação visual e CTA final.",
      result:"#videoResult"
    };
  }

  if(type==="image"){

    const idea=
      $("#imageIdea").value.trim();

    const format=
      $("#imageFormat").value;

    return {
      prompt:
        "Crie um prompt profissional e detalhado para geração de imagem."+
        "\nImagem desejada: "+idea+
        "\nFormato: "+format+
        "\nDescreva composição, iluminação, câmera, ambiente, "+
        "estilo visual e detalhes importantes.",
      result:"#imageResult"
    };
  }

  if(type==="voice"){

    const text=
      $("#voiceText").value.trim();

    const style=
      $("#voiceStyle").value;

    return {
      prompt:
        "Prepare este texto para uma narração profissional."+
        "\nEstilo de voz: "+style+
        "\nTexto:\n"+text+
        "\nMelhore ritmo, clareza e naturalidade sem mudar "+
        "desnecessariamente o sentido.",
      result:"#voiceResult"
    };
  }

  if(type==="music"){

    const theme=
      $("#musicTheme").value.trim();

    const style=
      $("#musicStyle").value.trim();

    const musicType=
      $("#musicType").value;

    const duration=
      $("#musicDuration").value;

    return {
      prompt:
        "Crie uma música original."+
        "\nTema ou título: "+theme+
        "\nEstilo/gênero: "+style+
        "\nTipo: "+musicType+
        "\nDuração aproximada: "+duration+
        "\nSe houver vocal, crie estrutura completa com versos, "+
        "refrão e ponte quando fizer sentido. "+
        "Inclua também uma descrição musical pronta para um gerador de música.",
      result:"#musicResult"
    };
  }

  if(type==="prompt"){

    const idea=
      $("#promptIdea").value.trim();

    return {
      prompt:
        "Transforme a ideia abaixo em um prompt profissional, "+
        "claro, detalhado e pronto para copiar e usar em uma IA."+
        "\nObjetivo:\n"+idea,
      result:"#promptResult"
    };
  }

  if(type==="site"){

    const name=
      $("#siteName").value.trim();

    const idea=
      $("#siteIdea").value.trim();

    return {
      prompt:
        "Planeje um site ou aplicativo profissional."+
        "\nNome: "+name+
        "\nProjeto: "+idea+
        "\nDefina objetivo, público, páginas ou telas, "+
        "funcionalidades, estrutura e experiência do usuário.",
      result:"#siteResult"
    };
  }

  if(type==="education"){

    const idea=
      $("#educationIdea").value.trim();

    return {
      prompt:
        "Ensine o assunto abaixo de forma clara e didática."+
        "\nAssunto:\n"+idea+
        "\nExplique passo a passo e use exemplos quando ajudarem.",
      result:"#educationResult"
    };
  }

  if(type==="professional"){

    const idea=
      $("#professionalIdea").value.trim();

    return {
      prompt:
        "Crie um material profissional pronto para uso "+
        "com base neste pedido:\n"+idea,
      result:"#professionalResult"
    };
  }

  if(type==="business"){

    const idea=
      $("#businessIdea").value.trim();

    return {
      prompt:
        "Analise esta necessidade empresarial e crie uma solução prática."+
        "\nNecessidade:\n"+idea+
        "\nOrganize a resposta com ações claras.",
      result:"#businessResult"
    };
  }

  if(type==="sales"){

    const idea=
      $("#salesIdea").value.trim();

    return {
      prompt:
        "Crie conteúdo profissional de vendas para este produto ou serviço:"+
        "\n"+idea+
        "\nInclua benefício principal, texto persuasivo, CTA "+
        "e sugestões adequadas para divulgação.",
      result:"#salesResult"
    };
  }

  if(type==="tools"){

    const idea=
      $("#toolsIdea").value.trim();

    return {
      prompt:
        "Crie uma solução ou ferramenta prática para esta necessidade:"+
        "\n"+idea+
        "\nExplique como ela deve funcionar e como implementar ou utilizar.",
      result:"#toolsResult"
    };
  }

  return null;
}

$$("[data-view]").forEach(button=>{

  button.onclick=()=>{
    view(button.dataset.view);
  };

});

$$("[data-generator]").forEach(button=>{

  button.onclick=()=>{

    const config=
      generatorPrompt(
        button.dataset.generator
      );

    if(!config)return;

    runGenerator(
      button,
      config.prompt,
      config.result
    );
  };

});

send.onclick=sendMessage;

input.onkeydown=event=>{

  if(
    event.key==="Enter"&&
    !event.shiftKey
  ){
    event.preventDefault();
    sendMessage();
  }
};

const voiceText=$("#voiceText");
const voiceCount=$("#voiceCount");

if(
  voiceText&&
  voiceCount
){

  voiceText.addEventListener(
    "input",
    ()=>{
      voiceCount.textContent=
        voiceText.value.length;
    }
  );
}

$("#saveChannel").onclick=()=>{

  const name=
    $("#chName").value.trim();

  if(!name){

    alert(
      "Digite o nome do canal ou marca."
    );

    return;
  }

  const channels=
    getChannels();

  channels.push({
    name,
    platform:
      $("#chPlatform").value.trim(),
    niche:
      $("#chNiche").value.trim(),
    language:
      $("#chLanguage").value.trim(),
    rules:
      $("#chRules").value.trim()
  });

  setChannels(channels);

  renderChannels();

  $("#chName").value="";
  $("#chPlatform").value="";
  $("#chNiche").value="";
  $("#chLanguage").value="";
  $("#chRules").value="";
};

function openHelp(){
  help.classList.add("open");
}

function closeHelp(){
  help.classList.remove("open");
}

$("#helpSideBtn").onclick=
  openHelp;

$("#closeHelp").onclick=
  closeHelp;

help.onclick=event=>{

  if(event.target===help)
    closeHelp();
};

$("#helpSend").onclick=async()=>{

  const question=
    $("#helpInput").value.trim();

  const answer=
    $("#helpAnswer");

  if(!question){

    answer.textContent=
      "Digite sua dúvida sobre o ChatCreova.";

    return;
  }

  answer.textContent=
    "Pensando...";

  try{

    answer.textContent=
      await ollamaChat([
        {
          role:"system",
          content:
            "Você é o suporte do ChatCreova AI. "+
            "Responda em português do Brasil de forma simples, "+
            "curta e passo a passo. "+
            "Não invente funções que não existem."
        },
        {
          role:"user",
          content:question
        }
      ]);
  }
  catch(error){

    answer.textContent=
      errorMessage(error);
  }
};

renderChannels();
view("chat");
checkAI();

})();
