# CHATCREOVA AI — V23
# ARQUITETURA MESTRE

## PARTE 1 — FUNDAÇÃO OFICIAL

**Projeto:** ChatCreova AI  
**Versão de desenvolvimento:** V23  
**Versão estável preservada:** V22  
**Status da V22:** CONGELADA — NÃO ALTERAR  
**Objetivo da V23:** criar a fundação técnica necessária para conectar Queen, Gerente, especialistas, ferramentas e futuros workers de forma segura, modular, verificável e escalável.

---

# 1. REGRA PRINCIPAL DO PROJETO

A V23 NÃO substitui nem modifica a V22.

A V22 permanece como versão estável de referência.

Todo desenvolvimento novo deve acontecer exclusivamente na V23 ou em laboratório isolado.

Método oficial de desenvolvimento:

1. Preservar o que funciona.
2. Criar nova versão.
3. Implementar uma função ou módulo por vez.
4. Testar isoladamente.
5. Corrigir somente a nova versão.
6. Executar teste de regressão.
7. Comprovar funcionamento.
8. Aprovar.
9. Congelar a versão aprovada.
10. Somente então avançar para o próximo módulo.

Nenhuma versão estável será modificada diretamente por agentes ou automações.

---

# 2. PRINCÍPIO-MÃE DA V23

SUGERIR NÃO É DECIDIR.

EXECUTAR NÃO É VERIFICAR.

Nenhum componente de Inteligência Artificial possui autoridade para declarar uma tarefa como concluída.

Somente o Control Plane poderá alterar uma tarefa para:

COMPLETED

e somente depois de verificar deterministicamente que a execução realmente aconteceu e que o resultado esperado existe.

Uma mensagem de IA dizendo:

"Concluído"

"Finalizado"

"Arquivo criado"

"Tarefa executada"

NÃO constitui prova de execução.

---

# 3. ARQUITETURA GERAL

Fluxo planejado:

USUÁRIO
↓
QUEEN
↓
CONTROL PLANE
↓
GERENTE / PLANEJADOR
↓
ORQUESTRADOR DETERMINÍSTICO
↓
ESPECIALISTA
↓
WORKER / FERRAMENTA
↓
ARTEFATO / RESULTADO
↓
VERIFICAÇÃO
↓
CONTROL PLANE
↓
QUEEN
↓
USUÁRIO

A Queen continua sendo a principal interface de comunicação com o usuário.

O Control Plane será a autoridade central do sistema.

O Gerente poderá planejar e decompor tarefas.

O Orquestrador Determinístico decidirá tecnicamente como as tarefas válidas serão executadas.

Os especialistas executarão trabalhos dentro de seus limites.

Workers e ferramentas executarão as operações reais.

O Control Plane verificará o resultado antes de registrar conclusão.

---

# 4. CONTROL PLANE

O Control Plane será a camada central de controle da ChatCreova.

Ele deverá responder permanentemente a três perguntas:

1. O que foi solicitado?
2. O que está acontecendo?
3. O que foi comprovadamente produzido?

Responsabilidades iniciais:

- receber solicitações;
- validar contratos;
- gerar trace_id;
- registrar tarefas;
- controlar estados;
- despachar tarefas;
- controlar fila;
- registrar heartbeat;
- controlar timeout e cancelamento;
- armazenar referências de artefatos;
- verificar resultados;
- manter logs;
- controlar memória estruturada;
- montar context packets;
- entregar eventos para a Queen.

O Control Plane será a única autoridade sobre o estado oficial das tarefas.

---

# 5. BACKEND DA V23

Decisão inicial:

FASTAPI + PYTHON

Motivos principais:

- integração natural com o ecossistema de IA planejado;
- contratos validados;
- suporte assíncrono;
- suporte a streaming;
- integração futura com workers;
- documentação automática da API;
- separação clara entre frontend, controle e execução.

A V23 inicial NÃO precisa de arquitetura distribuída complexa.

O Control Plane poderá começar em um único ambiente local, organizado internamente em módulos independentes.

---

# 6. BANCO INICIAL

Banco da V23 inicial:

SQLITE

Configuração prevista:

- SQLite;
- WAL;
- camada de repositório;
- migrações controladas;
- IDs UUID/ULID;
- timestamps padronizados;
- arquivos grandes fora do banco;
- banco armazenando metadados, estados e referências.

SQLite será utilizado enquanto existir um único ambiente escrevendo no estado central.

Gatilho planejado para PostgreSQL:

Quando uma segunda máquina precisar escrever diretamente no mesmo estado compartilhado, a arquitetura deverá ser reavaliada para migração ao PostgreSQL.

---

# 7. FILA DE TAREFAS

A V23 NÃO começará com:

- Redis;
- Celery;
- RabbitMQ;
- Temporal.

Inicialmente, a fila será controlada pelo próprio banco.

Conceitos obrigatórios desde o começo:

- task_id;
- status;
- prioridade;
- attempts;
- max_attempts;
- idempotency_key;
- lease;
- heartbeat;
- timeout;
- cancelamento;
- dead-letter;
- retry controlado.

Interface conceitual da fila:

enqueue
claim
ack
fail
heartbeat
requeue
cancel

A implementação poderá ser substituída no futuro sem alterar Queen, Gerente ou especialistas.

---

# 8. QUEEN

A Queen continua sendo a interface principal com o usuário.

A Queen NÃO será descartada.

A V23 deve preservar o comportamento de streaming já validado na V22.

A Queen terá dois tipos conceituais de fluxo:

## FAST PATH

Para conversa normal.

Objetivo:

preservar uma experiência rápida e progressiva de conversa.

## TASK PATH

Para trabalhos que necessitem:

- especialista;
- ferramenta;
- worker;
- arquivo;
- projeto;
- execução verificável;
- tarefa longa;
- múltiplas etapas.

Nesse caminho, o Control Plane assume o controle operacional.

A Queen apresenta o progresso e o resultado, mas não inventa estados.

---

# 9. GERENTE

O Gerente será responsável por:

- interpretar objetivos complexos;
- propor planejamento;
- decompor trabalhos;
- sugerir especialistas;
- organizar dependências entre subtarefas.

O Gerente NÃO poderá:

- alterar diretamente o estado oficial da tarefa;
- declarar tarefa concluída;
- ignorar contratos;
- executar ferramentas arbitrariamente;
- pular verificações;
- modificar versões estáveis.

CrewAI permanece candidato para a camada de planejamento do Gerente.

Sua adoção definitiva dependerá de testes isolados posteriores.

---

# 10. ORQUESTRADOR DETERMINÍSTICO

O Orquestrador Determinístico é diferente do Gerente.

O Gerente sugere.

O Orquestrador valida.

Responsabilidades:

- verificar se a ação existe;
- verificar se o especialista existe;
- validar inputs;
- verificar capacidades disponíveis;
- verificar restrições;
- controlar ordem técnica;
- enfileirar;
- aplicar políticas;
- controlar retries;
- controlar timeout;
- controlar cancelamento;
- verificar evidência;
- autorizar transições de estado.

A Inteligência Artificial poderá propor.

O código determinístico decidirá se a proposta pode ser executada.

---

# 11. PRIMEIRO ESPECIALISTA DA V23

A primeira prova NÃO utilizará imagem, vídeo, música ou ferramentas pesadas.

Será criado apenas UM especialista textual simples.

Nome provisório:

ANALISTA DE TEXTO

Responsabilidade inicial:

- receber uma tarefa textual;
- receber contexto controlado;
- chamar o Qwen local;
- produzir resultado textual;
- entregar o resultado como artefato;
- permitir que o Control Plane valide a execução.

Esse especialista servirá para provar a fundação antes da entrada dos demais departamentos.

---

# 12. MODELO LOCAL ATUAL

Modelo atualmente utilizado:

qwen3.5:4b

Execução:

Ollama local

Ambiente observado:

- modelo: qwen3.5:4b;
- tamanho aproximado observado: 3.1 GB;
- processamento observado: 100% CPU;
- contexto observado: 4096.

A V23 deverá trabalhar respeitando esse limite real antes de qualquer tentativa de expansão.

Thinking deverá permanecer desativado nas tarefas estruturadas quando apropriado, evitando consumo desnecessário de contexto e processamento.

Nenhuma troca de modelo será feita apenas por hipótese.

Mudanças de modelo deverão ser testadas separadamente.

---

# 13. REGRA DE CONTEXTO

CONTEXTO NÃO É MEMÓRIA.

A V23 não deverá simplesmente enviar todo o histórico da conversa ao modelo.

Será criado um CONTEXT PACKET controlado.

O pacote poderá conter:

- identidade/instruções necessárias;
- projeto ativo;
- entidade ativa;
- preferências relevantes;
- resumo necessário;
- últimos turnos relevantes;
- referências de artefatos;
- objetivo da tarefa;
- restrições;
- schema de saída.

O tamanho deverá respeitar o orçamento real do modelo.

Informações menos importantes deverão ser descartadas antes que informações essenciais.

O servidor NÃO deverá depender de truncamento silencioso do modelo.

---

# 14. CONTINUIDADE DE PROJETO

Problema observado na V22:

Quando solicitado a continuar uma campanha anterior, o modelo pode produzir uma campanha diferente porque não possui uma referência estruturada confiável.

Solução da V23:

Referências importantes deverão possuir IDs.

Exemplos:

project_id
campaign_id
artifact_id
task_id
session_id

Quando o usuário disser:

"continue a campanha anterior"

o sistema deverá primeiro resolver deterministicamente qual campanha está sendo referenciada.

Depois deverá inserir explicitamente essa referência no context packet.

Exemplo conceitual:

ENTIDADE_ATIVA:
campaign_id = X
nome = Campanha Cafeteria Premium
last_task_id = Y
last_artifact_id = Z

Se houver mais de uma referência plausível, a Queen deverá perguntar qual delas o usuário deseja.

REGRA:

AMBIGUIDADE → PERGUNTAR.

NUNCA CHUTAR.

---

# 15. MEMÓRIA

A memória será separada em escopos.

Escopos iniciais:

1. Sessão/Conversa
2. Usuário
3. Projeto
4. Especialista
5. Tarefa

Persistir principalmente:

- IDs;
- entidades;
- decisões;
- preferências relevantes;
- projetos;
- artefatos;
- tarefas;
- eventos;
- resumos estruturados;
- procedência das informações.

Não transformar todo o histórico bruto em memória permanente.

O modelo NÃO poderá gravar memória silenciosamente por conta própria.

Informações promovidas para memória deverão possuir procedência e processo controlado.

---

# 16. REGRA DE PROVA DE EXECUÇÃO

Uma tarefa somente poderá atingir COMPLETED depois de validação real.

Dependendo do tipo de tarefa, a evidência poderá incluir:

- retorno real do worker;
- exit code válido;
- arquivo existente;
- tamanho maior que zero;
- hash recalculado;
- MIME verificado;
- arquivo decodificável;
- JSON válido;
- schema válido;
- recibo de ação externa;
- métricas de execução;
- resultado estruturado.

Se uma tarefa deveria criar um arquivo e nenhum arquivo válido foi produzido:

FAILED.

Se a IA disser "concluí", mas a verificação falhar:

FAILED.

A verdade do sistema vem da evidência, não da mensagem da IA.

---

# 17. PRINCÍPIO DE ISOLAMENTO

A falha de um módulo NÃO poderá derrubar toda a ChatCreova.

Exemplos:

Maestro falhou:
Queen continua funcionando.

Narrador falhou:
Queen e outros especialistas continuam funcionando.

Ollama caiu:
API permanece ativa e informa dependência indisponível.

Worker morreu:
lease expira e a tarefa poderá ser recuperada conforme política.

Arquivo corrompido:
artefato é bloqueado e não entregue como válido.

Cada módulo deverá possuir limites claros de falha.

---

# 18. ENGENHEIRO

OpenHands permanece candidato para o módulo Engenheiro.

Fluxo obrigatório:

PRODUÇÃO READ-ONLY
↓
CÓPIA DE LABORATÓRIO
↓
ALTERAÇÃO
↓
TESTES
↓
REGRESSÃO
↓
LOGS
↓
APROVAÇÃO HUMANA
↓
NOVA VERSÃO

O Engenheiro NÃO poderá modificar diretamente V21, V22 ou qualquer versão congelada.

A correção sempre nasce como nova versão ou patch isolado.

---

# 19. REGRA DE VERSIONAMENTO

VERSÃO ESTÁVEL É IMUTÁVEL.

V22:
CONGELADA.

V23:
LABORATÓRIO / DESENVOLVIMENTO.

Quando uma versão futura for aprovada:

- registrar;
- congelar;
- preservar;
- nunca corrigir diretamente;
- correções nascem na versão seguinte.

---

# FIM DA PARTE 1
# CONTINUA NA PARTE 2# PARTE 2 — CONTRATOS, ARTEFATOS, SEGURANÇA E OBSERVABILIDADE

# 20. CONTRATO DE TAREFA

Toda tarefa executável na ChatCreova deverá possuir um contrato estruturado.

Campos-base:

- task_id
- trace_id
- user_id
- project_id
- parent_task_id
- specialist
- specialist_version
- action
- inputs
- constraints
- priority
- status
- progress
- attempt
- max_attempts
- idempotency_key
- required_capabilities
- lease_owner
- lease_expires_at
- heartbeat_at
- deadline_at
- timeout_s
- cancel_requested
- created_at
- updated_at
- started_at
- finished_at
- error
- result
- result_ref
- evidence
- verification
- usage
- schema_version
- created_by

Os inputs deverão ser validados ANTES da execução.

Input inválido não deve gastar processamento do modelo ou ferramenta.

---

# 21. ESTADOS DE TAREFA

Estados previstos:

QUEUED
RUNNING
WAITING_INPUT
WAITING_DEPENDENCY
WAITING_CAPABILITY
COMPLETED
COMPLETED_WITH_WARNINGS
FAILED
CANCELED
DEAD_LETTER

Cancelamento solicitado deverá ser registrado separadamente antes do encerramento efetivo.

Nenhuma IA poderá escrever diretamente esses estados.

A transição pertence ao Control Plane.

---

# 22. CONTRATO DE ARTEFATO

Todo resultado persistente deverá possuir identidade própria.

Campos-base:

- artifact_id
- user_id
- project_id
- source_task_id
- producer
- type
- mime
- version
- storage_location
- storage_backend
- size_bytes
- hash
- hash_algorithm
- status
- verify_status
- verified_at
- metadata
- created_at
- created_by
- parent_artifacts
- supersedes_artifact_id
- visibility
- access_scope
- immutable
- expires_at
- retention
- usage
- preview_ref

Tipos iniciais:

- text
- image
- video
- audio
- document

Estados conceituais:

PENDING
MATERIALIZING
READY
CORRUPT
FAILED
DELETED

READY somente poderá ser concedido depois da verificação.

---

# 23. RASTREABILIDADE DE ARTEFATOS

Um artefato deverá poder indicar de onde veio.

Relações possíveis:

- derived_from
- thumbnail_of
- render_of
- copy_of
- version_of
- generated_from

Exemplo:

Vídeo final
↓
derivado de cenas
↓
derivadas de imagens
↓
derivadas de roteiro
↓
derivado da tarefa original.

Isso permitirá reconstruir a origem de um resultado.

---

# 24. STORAGE

Arquivos grandes NÃO serão armazenados diretamente no SQLite.

O banco guardará:

- ID;
- caminho;
- hash;
- MIME;
- tamanho;
- proprietário;
- projeto;
- versão;
- metadados;
- relações;
- estado de verificação.

O conteúdo físico ficará no sistema de armazenamento.

Na V23 inicial:

ARMAZENAMENTO LOCAL.

No futuro poderá existir adaptador para:

- outro disco;
- NAS;
- segundo computador;
- servidor;
- object storage;
- cloud storage.

Queen e especialistas não deverão depender do local físico do arquivo.

Eles trabalharão com artifact_id.

---

# 25. VERIFICAÇÃO DE ARTEFATO

O Control Plane deverá revalidar resultados.

Nunca confiar apenas na declaração do worker.

Exemplos:

## TEXTO / JSON

- conteúdo existe;
- tamanho válido;
- encoding válido;
- JSON faz parse quando aplicável;
- schema válido.

## IMAGEM

- arquivo existe;
- tamanho > 0;
- MIME compatível;
- imagem realmente decodifica;
- dimensões válidas;
- hash confirmado.

## ÁUDIO

- arquivo existe;
- container válido;
- duração detectável;
- decodificação possível;
- hash confirmado.

## VÍDEO

- arquivo existe;
- container válido;
- duração detectável;
- estrutura necessária presente;
- decodificação possível;
- hash confirmado.

A validação específica será criada quando cada especialista for ativado.

---

# 26. EVENT LOG

A V23 deverá registrar eventos de forma append-only.

Uma ocorrência registrada não deve simplesmente desaparecer porque o estado atual mudou.

Tabela conceitual:

task_events

Cada evento deverá registrar quando aplicável:

- event_id
- trace_id
- session_id
- user_id
- project_id
- task_id
- attempt_id
- artifact_id
- worker_id
- timestamp
- stage
- component
- event
- status_before
- status_after
- duration_ms
- error_code
- payload resumido

Objetivo:

permitir reconstruir exatamente o caminho de uma tarefa.

---

# 27. TRACE

Cada turno importante deverá receber um:

trace_id

Esse ID acompanha o trabalho ponta a ponta.

Exemplo:

queen.received
↓
task.created
↓
orchestrator.routed
↓
specialist.started
↓
worker.exec
↓
evidence.verified
↓
task.completed
↓
queen.streamed

Objetivo futuro:

consultar um único trace_id e entender tudo que aconteceu.

Isso elimina diagnóstico baseado apenas em suposição.

---

# 28. OBSERVABILIDADE

Métricas mínimas:

- tempo de fila;
- tempo de execução;
- duração total;
- sucesso;
- falha;
- error_code;
- retries;
- timeout;
- artefatos produzidos;
- tokens de entrada;
- tokens de saída;
- tokens por segundo;
- TTFT;
- saúde dos workers;
- uso de armazenamento;
- estado do banco.

Logs deverão ser estruturados.

Segredos não poderão aparecer nos logs.

---

# 29. USAGE EVENTS

Desde a fundação, a V23 deverá registrar consumo bruto.

Não definir preço comercial definitivo agora.

Registrar primeiro o que realmente foi utilizado.

Exemplos:

- prompt_tokens
- completion_tokens
- total_tokens
- eval_duration
- CPU time
- wall time
- memória utilizada
- GPU time futuro
- VRAM futura
- bytes escritos
- bytes lidos
- chamadas externas
- duração de mídia
- resolução
- quantidade de gerações

Tabela conceitual:

usage_events

Campos-base:

- event_id
- task_id
- user_id
- project_id
- trace_id
- resource_type
- unit
- quantity
- timestamp
- metadata

No futuro, um catálogo de preços poderá transformar consumo em créditos.

---

# 30. CRÉDITOS

A área de créditos continuará prevista na arquitetura.

Na V23 inicial:

SEM PAGAMENTO REAL.

Preparar apenas a fundação para:

- saldo;
- consumo;
- histórico;
- pacote;
- catálogo;
- transação;
- auditoria.

Preço não deve ficar hardcoded dentro dos especialistas.

No futuro:

CONSUMO REAL
×
CATÁLOGO VERSIONADO
=
CRÉDITOS COBRADOS

Assim uma alteração futura de preço não modifica o histórico antigo.

---

# 31. SEGURANÇA DESDE A FUNDAÇÃO

Proteções que devem nascer cedo:

- validação de entrada;
- autenticação da API quando aplicável;
- autorização por usuário/projeto;
- isolamento de projetos;
- proteção contra path traversal;
- segredos somente server-side;
- logs com redação de segredos;
- allowlist de ferramentas;
- timeout;
- limite de payload;
- rate limit quando necessário;
- auditoria;
- sandbox para execução de código;
- CORS restrito;
- nenhuma credencial no frontend.

Regra:

O frontend nunca deve conter segredos privados.

---

# 32. FRONTEND

Durante o desenvolvimento, a interface poderá continuar baseada no frontend atual.

A V22 permanece publicada e congelada.

A V23 será separada.

Possíveis ambientes de desenvolvimento:

1. Frontend servido pelo próprio backend local.
2. GitHub Pages comunicando-se com backend local devidamente configurado.
3. Futuramente backend remoto HTTPS.

Nenhuma decisão deverá quebrar a V22 existente.

---

# 33. STREAMING

O streaming é requisito funcional da Queen.

O usuário deve continuar vendo a resposta aparecer progressivamente.

O novo sistema poderá transmitir eventos como:

- token
- status
- progress
- artifact
- error
- done

Envelope conceitual:

task_id
seq
type
data

O número seq permitirá ordenar eventos e futuramente facilitar reconexão/replay.

REGRA:

O stream apresenta o estado.

O stream NÃO é a autoridade do estado.

A autoridade continua sendo o Control Plane.

---

# 34. FALHAS

Falhas deverão produzir estados claros.

## OLLAMA INDISPONÍVEL

Não derrubar a interface.

Registrar dependência indisponível.

Tarefa poderá aguardar ou falhar conforme política.

## ESPECIALISTA TRAVADO

Detectar por timeout, heartbeat ou lease.

Encerrar ou reassentar conforme política.

## WORKER MORTO

Lease expira.

Tarefa pode ser recolocada na fila.

## CAPACIDADE INDISPONÍVEL

Estado:

WAITING_CAPABILITY

## ARQUIVO CORROMPIDO

Não entregar como válido.

Marcar artefato:

CORRUPT

## USUÁRIO CANCELA

Registrar cancel_requested.

Enviar cancelamento ao worker.

Finalizar:

CANCELED

## FALHA REPETIDA

Mover para:

DEAD_LETTER

Nada deverá desaparecer silenciosamente.

---

# 35. RETRY

Retry deverá ser controlado.

Nunca criar loop infinito.

Cada ação deverá definir:

- retryable;
- max_attempts;
- backoff;
- timeout;
- idempotency.

Ações com efeito externo NÃO devem ser repetidas automaticamente sem garantia de idempotência.

Exemplo:

publicar algo duas vezes é diferente de gerar novamente um texto.

---

# 36. WORKERS

A arquitetura deverá falar em CAPACIDADES, não em hardware específico.

Exemplos de capacidades:

- text_generation
- image_generation
- video_generation
- audio_generation
- code_execution
- document_processing

O sistema superior não deverá precisar saber se a execução ocorre em:

- CPU local;
- GPU local;
- segundo computador;
- servidor;
- API externa;
- nuvem.

Essa decisão pertence à camada de workers/adaptadores.

---

# 37. REGISTRY DE WORKERS

Futuramente cada worker poderá anunciar:

- worker_id;
- capabilities;
- modelo;
- status;
- heartbeat;
- carga;
- endpoint;
- precisão;
- requisitos;
- tempo estimado.

Assim, trocar hardware não exige reescrever Queen ou Gerente.

---

# 38. SEGUNDO COMPUTADOR / GPU

A arquitetura já deverá permitir crescimento futuro.

Hoje:

CPU LOCAL.

Amanhã poderá existir:

GPU LOCAL
ou
SEGUNDO COMPUTADOR
ou
SERVIDOR
ou
CLOUD API.

Quando uma segunda máquina precisar compartilhar escrita do estado central, reavaliar SQLite e migrar para PostgreSQL.

O hardware não deverá ser codificado diretamente na lógica dos especialistas.

---

# 39. ESCRITÓRIO

OpenClaw permanece candidato para o módulo Escritório.

Princípio:

PRIVILÉGIO POR TAREFA.

O Escritório deverá receber somente o acesso necessário para executar aquela tarefa.

Não deverá possuir acesso irrestrito ao computador.

Restrições planejadas:

- pasta do projeto;
- sem acesso ao sistema operacional inteiro;
- sem acesso ao billing;
- sem acesso aos segredos;
- sem acesso automático a outros projetos;
- credenciais temporárias quando necessário;
- ações destrutivas controladas;
- envio/publicação com política própria;
- auditoria de ferramentas.

---

# 40. ESPECIALISTAS PLANEJADOS

Estrutura atual planejada:

## QUEEN
Interface principal e conversa.

## GERENTE
Planejamento e decomposição.

## ESCRITÓRIO
Arquivos, produtividade, integrações e automações.

## ENGENHEIRO
Diagnóstico, código, testes e manutenção em sandbox.

## PROFESSOR
Ensino e orientação estruturada.

## MAESTRO
Produção musical.

## DIRETOR DE ARTE
Imagem e criação visual.

## DIRETOR DE VÍDEO
Geração de vídeo.

## NARRADOR
Voz e narração.

## EDITOR DE VÍDEO
Montagem e pós-produção.

## DIRETOR DE VIDEOCLIPE
Coordenação de produção audiovisual musical.

## SAÚDE
Informação e orientação geral dentro dos limites definidos.

## JURÍDICO / DIREITOS DO TRABALHADOR
Informação jurídica geral, com foco inicial no Brasil e fontes apropriadas.

## APOIO EMOCIONAL
Suporte conversacional seguro dentro dos limites definidos.

## VENDEDOR
Conteúdo comercial e social commerce sem inventar informações do produto.

Todos permanecem:

EM CONSTRUÇÃO

até serem ativados e testados individualmente.

---

# 41. REGRA DE ATIVAÇÃO DOS ESPECIALISTAS

Não conectar vários especialistas simultaneamente.

Sequência:

FUNDAÇÃO
↓
TESTE
↓
PRIMEIRO ESPECIALISTA
↓
TESTE
↓
CONGELAR
↓
SEGUNDO ESPECIALISTA
↓
TESTE
↓
CONGELAR
↓
CONTINUAR

Cada especialista deve possuir módulo independente.

Falha de um não poderá destruir os demais.

---

# 42. ESTRUTURA INTERNA PADRÃO DE UM ESPECIALISTA

Cada especialista deverá possuir, quando aplicável:

- interface/configuração;
- persona/instruções;
- ferramentas;
- engines;
- conectores;
- APIs;
- presets;
- modelos;
- projetos;
- arquivos;
- memória;
- contexto;
- tarefas;
- status;
- histórico;
- versões;
- logs;
- diagnósticos;
- testes;
- sandbox;
- permissões;
- segurança;
- custo/uso;
- exportação;
- integração com Gerente;
- integração com outros departamentos.

Essa estrutura serve como padrão, não como obrigação de implementar tudo no primeiro dia.

---

# 43. ORDEM DE CONSTRUÇÃO

Ordem-base planejada:

FASE 0
Baseline e medições.

FASE 1
Control Plane + contratos + estados + logs.

FASE 2
Artefatos + storage + memória/contexto.

FASE 3
Fila + máquina de estados + prova de execução.

FASE 4
Integração controlada da Queen.

FASE 5
Gerente/orquestração + primeiro especialista textual.

Depois da fundação aprovada:

- Escritório;
- Narrador;
- Arte;
- Maestro;
- Vídeo;
- Editor;
- Videoclipe;
- Vendedor;
- módulos sensíveis;
- créditos/pagamentos.

A ordem poderá ser ajustada com base em testes reais.

---

# 44. PROTÓTIPO MÍNIMO V23

Primeiro fluxo completo:

USUÁRIO
↓
QUEEN
↓
CONTROL PLANE
↓
ORQUESTRADOR
↓
ANALISTA DE TEXTO
↓
QWEN LOCAL
↓
ARTEFATO TEXTUAL
↓
VERIFICAÇÃO
↓
CONTROL PLANE
↓
QUEEN
↓
USUÁRIO

Sem:

- imagem;
- vídeo;
- música;
- pagamento;
- publicação;
- automação externa pesada.

Objetivo:

provar a estrada antes de colocar os veículos pesados.

---

# 45. CINCO TABELAS INICIAIS

Estrutura mínima conceitual:

1. tasks
2. task_events
3. artifacts
4. memory_records
5. sessions

Outras tabelas poderão surgir conforme necessidade comprovada.

usage_events deverá ser incorporada cedo para registrar consumo real.

---

# 46. TESTE DE CONTINUIDADE

Teste obrigatório:

TURNO 1:

Criar campanha A.

O sistema registra:

campaign_id = A

TURNO 2:

Usuário:

"Continue a campanha anterior."

PASS:

Sistema resolve campaign_id = A antes da geração.

FAIL:

Modelo cria campanha B sem solicitação.

Esse teste deverá fazer parte da aprovação da fundação.

---

# 47. TESTE DE FALSA CONCLUSÃO

Criar tarefa que exige artefato.

Forçar resposta textual:

"Concluído."

sem produzir artefato.

PASS:

Tarefa NÃO chega a COMPLETED.

FAIL:

Sistema aceita a declaração da IA como evidência.

---

# 48. TESTE DE FALHA DO OLLAMA

Durante uma tarefa de teste:

interromper Ollama.

PASS:

- Control Plane continua vivo;
- frontend continua vivo;
- erro é registrado;
- tarefa recebe estado apropriado;
- nenhum outro módulo é destruído.

FAIL:

queda do Ollama derruba todo o sistema.

---

# 49. TESTE DE WORKER

Iniciar tarefa.

Interromper worker antes da conclusão.

PASS:

- heartbeat para;
- lease expira;
- tarefa não fica eternamente RUNNING;
- sistema aplica política de recuperação.

FAIL:

tarefa fica presa indefinidamente.

---

# 50. REGRA PARA O SEGUNDO ESPECIALISTA

O segundo especialista NÃO será conectado apenas porque o primeiro respondeu corretamente.

A FUNDAÇÃO inteira deverá estar aprovada.

Só avançar quando os critérios de aprovação definidos para a V23 estiverem comprovados.

---

# FIM DA PARTE 2
# CONTINUA NA PARTE 3 — CHECKLIST FINAL V23# PARTE 3 — CHECKLIST OFICIAL DE APROVAÇÃO DA V23

# 51. REGRA DO CHECKLIST

A fundação da V23 somente será considerada aprovada quando TODOS os critérios obrigatórios forem testados.

Cada item deverá receber:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

Não conectar o segundo especialista enquanto existir qualquer item obrigatório em FAIL ou ainda não testado.

---

# 52. TESTE 01 — BACKEND FASTAPI

Objetivo:

Comprovar que o backend central sobe corretamente.

PASS se:

- FastAPI inicia;
- API responde;
- contratos são validados;
- erros de entrada são tratados;
- trace_id é criado.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 53. TESTE 02 — V22 INTACTA

Objetivo:

Garantir que a nova arquitetura não alterou nossa versão estável.

PASS se:

- nenhum arquivo V22 foi modificado;
- V22 continua abrindo;
- Queen da V22 continua respondendo;
- streaming da V22 continua funcionando.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

REGRA:

V22 NÃO SERÁ MODIFICADA PARA CORRIGIR V23.

---

# 54. TESTE 03 — STREAMING

Objetivo:

Preservar a resposta progressiva da Queen.

PASS se:

- tokens aparecem progressivamente;
- interface não precisa esperar a geração inteira;
- conexão permanece estável;
- finalização do stream é detectada corretamente.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 55. TESTE 04 — CAMINHO DUPLO DA QUEEN

Objetivo:

Separar conversa de trabalho executável.

PASS se:

CONVERSA NORMAL
→ fast path

TAREFA EXECUTÁVEL
→ Control Plane

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 56. TESTE 05 — FILA MÍNIMA

Objetivo:

Comprovar a fila sem infraestrutura externa.

PASS se:

- tarefa pode ser enfileirada;
- worker pode fazer claim;
- lease é registrado;
- heartbeat funciona;
- tarefa pode ser finalizada;
- nenhuma dependência de Redis é necessária.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 57. TESTE 06 — ESTADO AUDITÁVEL

Objetivo:

Registrar todas as mudanças importantes.

PASS se cada transição registra:

- task_id;
- trace_id;
- timestamp;
- ator/componente;
- estado anterior;
- estado novo.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 58. TESTE 07 — AUTORIDADE DE ESTADO

Objetivo:

Impedir agentes de alterarem o estado oficial.

PASS se:

- Queen não escreve status;
- Gerente não escreve status;
- especialista não escreve status;
- worker não escreve status oficial;
- somente Control Plane/orquestrador autorizado realiza a transição.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 59. TESTE 08 — GATE DE EVIDÊNCIA

Objetivo:

Impedir conclusão falsa.

PASS se:

uma tarefa que exige artefato NÃO consegue chegar a COMPLETED sem artefato verificado.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 60. TESTE 09 — VERIFICAÇÃO REAL

Objetivo:

Comprovar que o artefato existe de verdade.

PASS se:

- arquivo existe;
- tamanho é válido;
- hash é recalculado;
- tipo é validado;
- conteúdo pode ser aberto/decodificado conforme o formato.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 61. TESTE 10 — IA DIZ "CONCLUÍ"

Teste proposital:

fazer o especialista retornar:

"Concluí a tarefa."

sem gerar o artefato obrigatório.

PASS se:

status final = FAILED

FAIL se:

status final = COMPLETED

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 62. TESTE 11 — CONTINUIDADE DE CAMPANHA

TURNO 1:

Criar campanha.

Registrar:

campaign_id = A

TURNO 2:

"Continue a campanha anterior."

PASS se:

resolved_campaign_id = A

antes da chamada ao modelo.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 63. TESTE 12 — AMBIGUIDADE

Preparar duas campanhas plausíveis.

Usuário:

"Continue aquela campanha."

PASS se:

Queen pergunta qual campanha.

FAIL se:

sistema escolhe uma aleatoriamente.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 64. TESTE 13 — ORÇAMENTO DE CONTEXTO

Objetivo:

Respeitar o limite real do modelo.

PASS se:

- contexto é contado;
- orçamento é aplicado;
- partes menos importantes podem ser descartadas;
- cabeçalho essencial permanece;
- sistema não depende de truncamento silencioso.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 65. TESTE 14 — CONTEXT PACKET PERSISTIDO

Objetivo:

Poder reproduzir posteriormente o contexto usado.

PASS se:

a tarefa registra qual context_packet foi realmente enviado.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 66. TESTE 15 — MEMÓRIA CONTROLADA

Objetivo:

Impedir memória silenciosa criada pelo modelo.

PASS se:

uma informação somente é promovida para memória por processo autorizado e com procedência.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 67. TESTE 16 — OLLAMA FORA DO AR

Procedimento:

iniciar ambiente de teste e interromper Ollama.

PASS se:

- API continua viva;
- frontend continua vivo;
- erro é registrado;
- tarefa recebe estado apropriado;
- sistema não declara conclusão.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 68. TESTE 17 — WORKER INTERROMPIDO

Procedimento:

interromper worker durante execução.

PASS se:

- heartbeat para;
- lease expira;
- tarefa é recuperada/reassentada conforme política;
- não fica eternamente RUNNING.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 69. TESTE 18 — CANCELAMENTO

Usuário cancela uma tarefa em andamento.

PASS se:

- cancel_requested é registrado;
- worker recebe solicitação;
- estado terminal é CANCELED;
- repetir cancelamento não causa corrupção.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 70. TESTE 19 — TRACE COMPLETO

Objetivo:

Reconstruir um turno inteiro usando apenas trace_id.

PASS se é possível visualizar:

Queen
→ tarefa
→ orquestrador
→ especialista
→ worker
→ verificação
→ conclusão
→ retorno.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 71. TESTE 20 — USAGE EVENTS

Objetivo:

Registrar consumo desde a primeira versão da fundação.

PASS se são registrados quando disponíveis:

- tokens de entrada;
- tokens de saída;
- duração;
- CPU;
- bytes;
- chamadas;
- recurso utilizado.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 72. TESTE 21 — CONTRATOS

PASS se:

contrato de tarefa e contrato de artefato possuem os campos essenciais definidos na arquitetura.

Verificar especialmente:

- user_id;
- project_id;
- trace_id;
- source_task_id;
- idempotency_key;
- evidence;
- verification;
- usage;
- ownership;
- versionamento.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 73. TESTE 22 — HARDWARE DESACOPLADO

Objetivo:

Não amarrar arquitetura à máquina atual.

PASS se:

o sistema solicita CAPACIDADE.

Exemplo:

text_generation

e NÃO possui lógica central rígida como:

if GPU
if computador_2
if servidor_X

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 74. TESTE 23 — MIGRAÇÃO DE BANCO PREPARADA

Objetivo:

Evitar reescrever a plataforma quando PostgreSQL chegar.

PASS se:

- schema possui migrações;
- acesso ao banco é abstraído;
- IDs não dependem de rowid;
- arquivos não são blobs no banco;
- estrutura não depende desnecessariamente de recurso exclusivo do SQLite.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 75. TESTE 24 — FRONTEIRAS DOS COMPONENTES

PASS somente se:

QUEEN
→ conversa, intenção, apresentação.

GERENTE
→ planejamento e decomposição.

ORQUESTRADOR
→ validação, política, roteamento e estado.

ESPECIALISTA
→ execução especializada.

WORKER/FERRAMENTA
→ operação real.

CONTROL PLANE
→ autoridade e verificação.

Nenhum componente invade responsabilidade crítica de outro.

Resultado:

[ ] NÃO TESTADO
[ ] PASS
[ ] FAIL

---

# 76. REGRA 24/24

A fundação da V23 somente recebe:

V23 FUNDAÇÃO APROVADA

quando:

24 / 24 = PASS

Até lá:

V23 = LABORATÓRIO

Se qualquer teste falhar:

1. não conectar novo especialista;
2. localizar a falha;
3. corrigir somente V23;
4. executar novamente o teste;
5. executar regressão;
6. registrar resultado.

---

# 77. PRIMEIRO MARCO

Marco:

V23-FUNDACAO-01

Escopo:

- FastAPI;
- SQLite;
- Control Plane;
- tarefas;
- eventos;
- artefatos;
- memória mínima;
- context packet;
- fila;
- streaming;
- Analista de Texto;
- Qwen/Ollama;
- prova de execução;
- observabilidade mínima.

Nenhum módulo pesado entra neste marco.

---

# 78. DEPOIS DO 24/24

Somente depois da aprovação da fundação começará a integração progressiva dos departamentos.

Cada novo módulo deverá possuir seu próprio checklist.

Fluxo:

INTEGRAR
→ TESTAR ISOLADO
→ TESTAR INTEGRAÇÃO
→ TESTAR FALHA
→ APROVAR
→ CONGELAR
→ PRÓXIMO.

---

# 79. CONSULTORIA TÉCNICA EXTERNA

A ChatCreova poderá utilizar análises externas como apoio técnico.

Referências atuais:

CREAO / SuperAgent
→ revisão de arquitetura e sistemas de agentes.

Gemini
→ segunda análise técnica e comparação.

Regra:

Consultoria externa NÃO altera automaticamente o projeto.

Toda recomendação deverá ser comparada com:

- arquitetura aprovada;
- código real;
- testes reais;
- logs;
- limitações da máquina;
- segurança;
- estabilidade da versão atual.

Em caso de dúvida técnica importante:

1. documentar o problema;
2. reunir evidências;
3. formular pergunta específica;
4. consultar quando necessário;
5. comparar respostas;
6. decidir;
7. testar antes de incorporar.

---

# 80. REGRA DE OURO DA CHATCREOVA

PRESERVAR O QUE FUNCIONA.

NÃO ALTERAR VERSÃO ESTÁVEL.

UMA MUDANÇA POR VEZ.

UM MÓDULO POR VEZ.

TESTAR ISOLADAMENTE.

NÃO DECLARAR CONCLUSÃO SEM EVIDÊNCIA.

FALHA DE UM MÓDULO NÃO DERRUBA OS OUTROS.

VERSÃO APROVADA É CONGELADA.

NOVA MELHORIA = NOVA VERSÃO.

---

# STATUS ATUAL

V22:
ESTÁVEL / CONGELADA.

V23:
FUNDAÇÃO EM CONSTRUÇÃO.

PRÓXIMO OBJETIVO:

V23-FUNDACAO-01
→ implementar e alcançar 24/24 PASS.

---

# FIM DO DOCUMENTO

CHATCREOVA AI
V23 — ARQUITETURA MESTRE
