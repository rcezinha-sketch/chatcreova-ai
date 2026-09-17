let selected='Criar Prompt Profissional';
document.querySelectorAll('[data-tool]').forEach(b=>b.onclick=()=>{selected=b.dataset.tool;document.getElementById('toolTitle').textContent=selected;document.getElementById('idea').focus();});
document.querySelectorAll('.formats button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.formats button').forEach(x=>x.classList.remove('active'));b.classList.add('active')});
document.getElementById('generate').onclick=()=>{
 const idea=document.getElementById('idea').value.trim();
 const format=document.querySelector('.formats .active').textContent;
 const out=document.getElementById('result');
 if(!idea){out.classList.remove('hidden');out.textContent='Escreva uma ideia primeiro para testar o fluxo.';return}
 out.classList.remove('hidden');
 out.textContent=`DEMONSTRAÇÃO — ${selected}\nFormato: ${format}\n\nSua ideia:\n${idea}\n\n✓ Fluxo funcionando. Nesta primeira versão nenhuma API paga está conectada, portanto nenhum crédito real foi consumido.`;
};