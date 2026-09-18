CHATCREOVA AI — V14 — CORREÇÃO CIRÚRGICA DA V13

OBJETIVO
Corrigir os dois problemas confirmados no JavaScript real da V13:
1. navegação/interface misturada ao processamento do prompt;
2. tarefas marcadas SUCCESS e PRONTO sem artefato comprovado.

REGRAS V14
- Navegação só ocorre por ação manual do usuário.
- Processamento interno não pode chamar openView.
- Gerente permanece dono da conversa.
- Tema não define sozinho o formato de saída.
- "Daniel na cova dos leões" isolado pede esclarecimento do tipo de entrega.
- Funcionário SUCCESS exige artifactId.
- QA exige artefato válido.
- Sem QA aprovado, não existe PRONTO.
- Imagem/áudio/vídeo externo não são simulados quando provider está desligado.
- Texto, roteiro, narração, prompt, documento e código podem ser artefatos estruturados reais.
- Nenhuma API paga adicionada. Custo R$0.

TESTES-ALVO
A. "Crie uma imagem de Daniel na cova dos leões" -> fica no Gerente; provider desligado; NÃO PRONTO.
B. "Faça um roteiro sobre Daniel na cova dos leões" -> roteiro textual real.
C. "Crie um vídeo de 60 segundos sobre superação, com narração, 8 cenas, prompts, título, descrição, CTA e hashtags" -> 8 cenas + pacote.
D. "Daniel na cova dos leões" -> pergunta qual tipo de entrega.
E. Prompt no Gerente -> processamento não muda currentView.

OBSERVAÇÃO
Esta é uma V14 separada. A V13 não deve ser apagada.
