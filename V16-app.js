
(() => {
  "use strict";

  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];

  const input = $("#input");
  const messages = $("#messages");
  const help = $("#help");

  const KEY = "chatcreova_v16_channels";

  const OLLAMA_URL = "http://127.0.0.1:11434";
  const MODEL = "qwen3.5:4b";

  const history = [
    {
      role: "system",
      content:
        "Você é o ChatCreova AI, assistente oficial da plataforma ChatCreova. " +
        "Responda em português do Brasil por padrão, a menos que o usuário peça outro idioma. " +
        "Converse naturalmente e execute o pedido do usuário. " +
        "Entregue respostas completas e úteis, sem placeholders. " +
        "Não exponha raciocínio interno. " +
        "Não diga que você é Qwen espontaneamente. " +
        "Se perguntarem qual motor ou modelo está sendo usado, seja transparente e explique que o ChatCreova está usando um modelo Qwen executado localmente pelo Ollama. " +
        "Quando o usuário pedir roteiro, descrição, prompt, texto, planejamento, código ou outro conteúdo, produza o conteúdo solicitado em vez de apenas explicar como fazê-lo."
    }
  ];

  function view(id) {
    $$(".view").forEach(v => {
      v.classList.toggle("active", v.id === id);
    });
  }

  function fill(t) {
    view("chat");
    input.value = t;
    input.focus();
  }

  function msg(role, text) {
    const d = document.createElement("div");
    d.className = "msg " + role;

    const b = document.createElement("b");
    b.textContent =
      role === "user"
        ? "Você"
        : "✦ ChatCreova AI";

    const p = document.createElement("p");
    p.textContent = text;

    d.append(b, p);
    messages.append(d);
    messages.scrollTop = messages.scrollHeight;

    return p;
  }

  function get() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "[]");
    } catch {
      return [];
    }
  }

  function set(x) {
    localStorage.setItem(KEY, JSON.stringify(x));
  }

  function render() {
    const a = get();
    const s = $("#channelSelect");
    const cards = $("#channelCards");

    s.innerHTML =
      '<option value="">Sem canal/marca selecionado</option>';

    cards.innerHTML = "";

    a.forEach((c, i) => {
      const o = document.createElement("option");
      o.value = i;
      o.textContent = c.name;
      s.append(o);

      const d = document.createElement("div");
      d.className = "panel";
      d.textContent =
        c.name +
        " — " +
        [c.platform, c.niche, c.language]
          .filter(Boolean)
          .join(" • ");

      cards.append(d);
    });
  }

  function selectedChannelContext() {
    const select = $("#channelSelect");

    if (!select || select.value === "") {
      return "";
    }

    const channels = get();
    const channel = channels[Number(select.value)];

    if (!channel) {
      return "";
    }

    return (
      "\n\nContexto do canal ou marca selecionado:\n" +
      "Nome: " + (channel.name || "") + "\n" +
      "Plataforma: " + (channel.platform || "") + "\n" +
      "Nicho: " + (channel.niche || "") + "\n" +
      "Idioma: " + (channel.language || "") + "\n" +
      "Regras: " + (channel.rules || "")
    );
  }

  function openHelp() {
    help.classList.add("open");
  }

  function closeHelp() {
    help.classList.remove("open");
  }

  async function ollamaChat(chatMessages) {
    const response = await fetch(
      OLLAMA_URL + "/api/chat",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: MODEL,
          messages: chatMessages,
          stream: false,
          think: false,
          keep_alive: "10m"
        })
      }
    );

    if (!response.ok) {
      throw new Error(
        "Ollama respondeu com erro HTTP " +
        response.status
      );
    }

    const data = await response.json();

    if (
      !data ||
      !data.message ||
      !data.message.content
    ) {
      throw new Error(
        "A IA não devolveu uma resposta válida."
      );
    }

    return data.message.content.trim();
  }

  async function checkAI() {
    try {
      const response = await fetch(
        OLLAMA_URL + "/api/tags"
      );

      if (!response.ok) {
        throw new Error();
      }

      const data = await response.json();

      const found =
        Array.isArray(data.models) &&
        data.models.some(
          m =>
            m.name === MODEL ||
            m.model === MODEL
        );

      const status =
        document.querySelector(
          ".ai-status, #aiStatus"
        );

      if (status) {
        status.textContent = found
          ? "• IA local conectada"
          : "• Modelo não encontrado";
      }

      return found;
    } catch {
      const status =
        document.querySelector(
          ".ai-status, #aiStatus"
        );

      if (status) {
        status.textContent =
          "• IA não conectada";
      }

      return false;
    }
  }

  async function sendMessage() {
    const t = input.value.trim();

    if (!t) return;

    msg("user", t);
    input.value = "";

    const waiting = msg(
      "ai",
      "Pensando..."
    );

    const userContent =
      t + selectedChannelContext();

    history.push({
      role: "user",
      content: userContent
    });

    $("#send").disabled = true;
    input.disabled = true;

    try {
      const answer =
        await ollamaChat(history);

      waiting.textContent = answer;

      history.push({
        role: "assistant",
        content: answer
      });
    } catch (error) {
      console.error(error);

      waiting.textContent =
        "Não consegui acessar a IA local. " +
        "Verifique se o Ollama está aberto no computador e tente novamente.";

      history.pop();
    } finally {
      $("#send").disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  $$("[data-view]").forEach(b => {
    b.onclick = () => view(b.dataset.view);
  });

  $$("[data-fill]").forEach(b => {
    b.onclick = () => fill(b.dataset.fill);
  });

  $("#send").onclick = sendMessage;

  input.onkeydown = e => {
    if (
      e.key === "Enter" &&
      !e.shiftKey
    ) {
      e.preventDefault();
      sendMessage();
    }
  };

  $("#saveChannel").onclick = () => {
    const n =
      $("#chName").value.trim();

    if (!n) {
      return alert(
        "Digite o nome do canal ou marca."
      );
    }

    const a = get();

    a.push({
      name: n,
      platform:
        $("#chPlatform").value.trim(),
      niche:
        $("#chNiche").value.trim(),
      language:
        $("#chLanguage").value.trim(),
      rules:
        $("#chRules").value.trim()
    });

    set(a);
    render();
  };

  $("#helpBtn").onclick = openHelp;
  $("#helpSideBtn").onclick = openHelp;
  $("#closeHelp").onclick = closeHelp;

  $("#helpSend").onclick = async () => {
    const helpInput =
      $("#helpInput");

    const helpAnswer =
      $("#helpAnswer");

    const question =
      helpInput
        ? helpInput.value.trim()
        : "";

    if (!question) {
      helpAnswer.textContent =
        "Digite sua dúvida sobre o ChatCreova.";
      return;
    }

    helpAnswer.textContent =
      "Pensando...";

    try {
      const answer =
        await ollamaChat([
          {
            role: "system",
            content:
              "Você é o Suporte IA do ChatCreova. " +
              "Responda em português do Brasil. " +
              "Ajude o usuário a utilizar a plataforma de forma simples, direta e passo a passo. " +
              "Não invente funções que não existem. " +
              "Se não souber se determinada função está disponível, diga isso claramente."
          },
          {
            role: "user",
            content: question
          }
        ]);

      helpAnswer.textContent = answer;
    } catch (error) {
      console.error(error);

      helpAnswer.textContent =
        "Não consegui acessar a IA local. Verifique se o Ollama está aberto.";
    }
  };

  help.onclick = e => {
    if (e.target === help) {
      closeHelp();
    }
  };

  render();
  view("chat");
  checkAI();
})();
