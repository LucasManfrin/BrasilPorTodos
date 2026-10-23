# Criar proposta acessível: modo guiado e modo manual

Estado em 2026-10-20. **Fluxo local implementado; UI-06 Preparado enquanto falta a avaliação com Gemini real.** [Roadmap](ROADMAP.md) · [Backlog](../project/BACKLOG.md#épico-ui-06--criar-proposta-acessível) · [ADR-040](../architecture/DECISIONS.md#adr-040--participação-local-acessível-e-assistência-opcional-gemini--2026-10-19).

## Começar simples, publicar com rigor

“Me ajuda a montar” e “Eu preencho” usam o mesmo molde. O primeiro apresenta uma pergunta por vez; o segundo organiza o preenchimento por etapas. É possível alternar sem perder respostas confirmadas, fontes e origem assistida. Salvar e retomar preserva o trabalho. A condução fixa funciona sem chave e sem chamadas a modelos; usar Gemini para desenvolver a ideia em linguagem de proposta é opcional.

Conta é obrigatória para salvar, compartilhar ou contribuir. Leitura de publicações e ideias explicitamente compartilhadas é pública. Salvar uma ideia não a torna pública.

| Nível | Requisitos | Destino |
| --- | --- | --- |
| IDEIA | Título e uma frase; valores, período e demais campos podem faltar | Privada inicialmente. Compartilhamento explícito com selo “ideia em construção”; pode receber sugestões de fontes e cópias atribuídas. Não entra no motor, planos ou ranking. |
| PROPOSTA COMPLETA | Checklist no servidor: problema, medida, financiamento, quem ganha/perde, riscos, fontes, período e estado fiscal aplicável | Publicação humana explícita cria versão imutável. Pode compor planos e, quando estimada com recortes compatíveis, a análise fiscal. |

“Não sei” não vira zero, fonte inventada nem confirmação automática. `NOT_ESTIMATED` impede promover uma ideia como completa. Uma justificativa de não aplicação fiscal (`NOT_APPLICABLE`) é admitida conforme checklist, sem parcelas inventadas e sem saldo fiscal calculado. A checklist não certifica eficácia, viabilidade jurídica ou verdade das alegações.

O compartilhamento cria uma fotografia pública explícita. Editar uma ideia compartilhada retira essa fotografia e volta a ideia para privada; é preciso compartilhar novamente. O novo conteúdo nunca fica público automaticamente. Sugestões não alteram o original; o autor decide o que aproveitar. Duplicações mantêm atribuição. Promoção encerra a ideia e remete à versão completa. Publicações e planos legados permanecem acessíveis, sem reclassificação, pontuação retroativa ou reescrita de snapshots.

## Roteiro e confirmações

O roteiro **1.0.0**, com oito perguntas fixas, está em `backend/app/modules/guidance/script.json`, acessível pela API e publicado na Metodologia do site. Texto e ordem não variam conforme tema ou posição. Inclui sempre “Quem poderia perder com isso?” e “O que poderia dar errado?”. [Perguntas e método](../data/METHODOLOGY.md#criação-guiada-e-sensibilidade-declarada--2026-10-19).

Depois de responder, a pessoa vê “Entendi isso” e confirma ou corrige. Nenhum campo é preenchido pela resposta sem confirmação. “Não sei” preserva a ausência. A IA não escolhe o roteiro, a posição política ou a publicação e não calcula. Por decisão posterior do mantenedor, pode sugerir caminhos de desenho e implantação, sempre separados da intenção declarada.

O assistente Gemini, com prompt 4.0.0, desenvolve a redação de política pública a partir da intenção informal: objetivo e mecanismo descritos pela pessoa. Retorna também sugestões concretas de desenho/implantação/contrapartidas e lacunas a investigar, separadas da redação principal. Título continua curto; etapas de conteúdo pedem elaboração útil. Não deve inventar dados, valores, anos, fontes, legislação ou efeitos comprovados nem escolher posição pelo autor. A tela compara original e proposta e permite manter o original. Sugestões começam desmarcadas; só entram no campo ao selecionar e confirmar, com rótulo “Sugestão de IA a avaliar”. Lacunas não viram respostas. O servidor confere somente estrutura e tamanho. Não compara números, URLs, unidades, negações, ressalvas ou posições entre original e sugestão. Orientações de conteúdo permanecem no prompt; a pessoa compara, aceita ou recusa. Não há certificação automática de fatos, sentido ou neutralidade. Resultados efetivamente gerados recebem origem “assistido por IA”, preservada ao alternar para manual e publicar. Fontes oficiais existentes são referências opcionais com data, sem busca de URL arbitrária e sem comprovação automática.

## Gemini opcional, consentimento e privacidade

O provedor fica atrás de uma interface trocável no backend. O escolhido pelo mantenedor é Gemini, com `GUIDANCE_MODEL=gemini-3.5-flash-lite`. Não há integração OpenAI. Chave apenas em `GEMINI_API_KEY` no ambiente do servidor; `GUIDANCE_AI_ENABLED=false` é o padrão. A chave já foi configurada no ambiente local. Uma geração fictícia real foi validada; sondagens também observaram HTTP 503 do provedor. Isso não encerra a avaliação sistemática de imparcialidade. [Configuração](../development/DEVELOPMENT.md#assistência-opcional-gemini).

O envio exige consentimento explícito para resposta atual e trechos já confirmados: até oito campos textuais, até 1.500 caracteres de cada na interface. Não inclui parcelas fiscais ou sugestões ainda não aceitas. O contexto pode estar incompleto; não é busca automática em fontes oficiais. Sem chave, limite atingido, falha ou resposta rejeitada, o texto continua disponível e o usuário segue sem IA. O limite padrão é 20 chamadas por usuário/dia UTC e cinco por minuto; tentativas inválidas/falhas também consomem quota. O limite diário é configurável.

Prompt, resposta, versão do roteiro/prompt/modelo e estado ficam em logs privados, com expiração padrão de sete dias, configurável entre um e 30. A pessoa pode apagar o conteúdo dos seus registros; contadores mínimos de quota são preservados. Apagamento vence resposta tardia de chamada pendente, evitando repovoar conteúdo apagado. Expiração exige limpeza executada com a aplicação/operação ativa; não prometer remoção com o computador desligado nem de backups históricos. O botão “Ver chamada e retorno da IA” consulta GET /api/v1/guidance/calls/{id}, ou GET /api/v1/guidance/calls/latest para a última chamada (inclusive falha), apenas para o autor autenticado, enquanto o registro não estiver apagado ou expirado. Mostra instrução, pergunta/resposta/contexto enviados, modelo/versões, saída registrada e uso, sem chave ou headers de autenticação. Não incluir conversas reais nos exemplos, relatórios públicos ou repositório.

## Análise comum de impacto

Nos dois modos, a tela final mostra checklist, dados ausentes e os mesmos resultados do motor. IDEIA permanece fora do cálculo. Depois de publicar como COMPLETA estimada, a análise usa a versão pública exata e apresenta valores declarados e sensibilidade ajustável. [Método `DECLARED_SENSITIVITY_1`](../data/METHODOLOGY.md#criação-guiada-e-sensibilidade-declarada--2026-10-19).

Sem premissas escolhidas, multiplicadores valem 1: a faixa coincide com o declarado. Não fabricar percentuais de incerteza. Parcelas com recortes ausentes/misturados, período inválido ou ausência de estimativa bloqueiam o resultado com explicação. Financiamento não vira receita adicional na conta.

A classificação disponível é **estimativa declarada**, sem atribuir automaticamente “efeito direto”, “especulativo” ou confiança estatística. O método não cobre impacto causal, propagação de grafos, emprego, PIB ou dívida. Categorias causais futuras dependem de evidência e método próprios.

## Participação e completude documental

Limites diários no servidor: dez ideias/cópias, 20 sugestões e dez denúncias por usuário, configuráveis. Denúncias têm tratamento administrativo com motivo e autoria; identidade do denunciante não aparece na leitura pública. Arquivamento remove a ideia da circulação pública sem alterar versões completas já publicadas.

O catálogo ordena propostas completas por **completude documental**, método `DOC_COMPLETENESS1`, e não popularidade: fonte vinculada vale um ponto; financiamento declarado diferente de `UNFUNDED` vale um; revisão técnica vale zero, marcada `NOT_ASSESSED`, porque esse fluxo de revisão de propostas ainda não existe. Máximo contratual três, máximo hoje alcançável dois. Empates usam data/identidade estáveis. Legado continua visível em grupo próprio, sem nota inferida. IDEIAs ficam fora do ranking. Isso não é nota de mérito político ou auditoria de fonte/custo.

## Fatias e aceite

| Item | Estado local | Evidência / pendência |
| --- | --- | --- |
| UI-06A | Concluído | Níveis, fotografia compartilhada, checklist, promoção, exclusões, atribuição e legado protegidos por integração |
| UI-06B | Concluído | Guiado/manual, confirmação, troca e retomada; fluxo conferido no navegador |
| UI-06C | Preparado | Roteiro, organizador trocável, consentimento, logs e limites implementados; configuração local e sondagem real feitas; avaliação sistemática e disponibilidade externa pendentes |
| UI-06D | Concluído no recorte declarado | Sensibilidade fiscal versionada pelo motor e lacunas explícitas; sem inferência causal ou selo de certeza |
| UI-06E | Concluído localmente | Limites, sugestões, denúncia/moderação e ordenação documental; lançamento público ainda exige governança e operação |
| UI-06F | Preparado | Casos de posições opostas e regressões com provedores controlados; falta avaliação registrada com o modelo real escolhido |

Os testes verificam identidade das perguntas, confirmação, “não sei”, privacidade, limites e formato. Alterações de redação e conteúdo são apresentadas para revisão humana, sem rejeição semântica automática. Não demonstram neutralidade universal de um modelo externo. Mudança de roteiro, prompt ou modelo exige repetir a avaliação antes de ativar assistência real. Evidências atuais em [VERIFICATION](../development/VERIFICATION.md). O épico não equivale ao lançamento público nem encerra magnitudes dos grafos.


Espera: GUIDANCE_TIMEOUT_SECONDS padrão 30 s, máximo 45 s; o proxy reserva 60 s somente para organizar resposta. Falhas não preenchem campos; a pessoa pode tentar novamente ou usar suas palavras sem IA. As perguntas permanecem fixas, e o assistente desenvolve a ideia com opções separadas para o autor avaliar. O roteiro continua 1.0.0; a mudança de prompt para 4.0.0 exige nova avaliação sistemática do modelo real.


## Experiência de criação — 2026-10-22

Aceite de IA único por criação/sessão: antes da primeira resposta, a pessoa escolhe aceitar o envio ao Gemini/retenção privada de até 7 dias, ou continuar sem IA. Nas perguntas seguintes vê “IA ativa · mudar”; revogar bloqueia chamadas futuras ao modelo. Aceite somente em memória, preservado ao trocar modo e transferido ao ID ao salvar. Reabrir em nova sessão ou iniciar outra criação exige nova escolha. A API recebe consentimento explícito em cada chamada real; não há mudança de autorização, retenção nem validação da saída.

O editor mantém uma pergunta por vez e confirmação humana, com original visível, texto organizado, caminhos selecionáveis, lacunas e rastreio recolhidos. Fluxo manual em cinco etapas, mesmo molde/checklist e prévia. [Inventário e decisões visuais](../design/WORKSPACE_AUDIT.md).


## Entradas distintas e revisão humana — 2026-10-22

Por decisão posterior do mantenedor, a captura rápida usa `/painel/ideias/nova`: título e uma frase, sempre privada no primeiro salvamento. A ação “Salvar e desenvolver com IA” salva antes de abrir o guiado no ID da ideia; consentimento continua antes de qualquer envio ao modelo. `/painel/propostas/nova` permanece o caminho para preparar a proposta completa, guiada ou manual, com etapas, financiamento, riscos, fontes e checklist. São níveis de maturidade do mesmo percurso: a ideia só entra em planos/cálculos depois de completa e explicitamente publicada. Abrir um formulário não publica nada.

Prompt 4.0.0 mantém instruções para desenvolver com fidelidade, evitar fatos inventados e apresentar alternativas separadas; a aceitação cabe à pessoa. Removidos os bloqueios semânticos do código, inclusive comparação de palavras, números, unidades, URLs, negações e proporção de expansão do texto. Limites técnicos de formato/campos, autenticação, consentimento, quotas, sigilo dos registros e contrato fiscal permanecem. Falha técnica de estrutura usa GUIDANCE_INVALID_OUTPUT; não é reprovação de conteúdo.
