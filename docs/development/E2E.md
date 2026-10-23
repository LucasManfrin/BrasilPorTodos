# Verificação do fluxo local da V1

Executada em 2026-10-06 no navegador interno, Windows, aplicação local e cluster PostgreSQL 18 isolado. Dados fictícios de contribuição ficaram somente no banco de demonstração, ignorado pelo Git. Dados de indicadores vieram das duas séries BCB verificadas.

| Cenário | Resultado |
| --- | --- |
| Cadastro → painel; login posterior | Passou |
| Recarregar a página e restaurar sessão com refresh/CSRF | Passou |
| Fonte HTTP/HTTPS; selecionar referência e descrever uso | Passou |
| Publicar proposta com nova despesa de `1234.56` e UNFUNDED | Exibiu R$ 1.234,56, premissas, fonte e histórico |
| Compor plano, simular e publicar | Total − R$ 1.234,56; linha por ano e aviso de financiamento |
| Sair e recarregar plano público | Consulta preservada sem login |
| Publicar proposta v2 com `9999.99` | Plano v1 continuou com proposta v1 e − R$ 1.234,56 |
| Indicador oficial → detalhe → página 2 do histórico | Unidade, conceito, coleta, fonte, licença e paginação visíveis |
| Painel administrativo → salvar definição sem alterar série | Autoria/data/motivo registrados; confirmação visível |
| Navegação por teclado, link “Ir para o conteúdo” | Foco em MAIN/conteudo após corrigir tabindex |
| Plano, indicador e painel em viewport de celular | Sem overflow horizontal da página; tabelas têm rolagem interna |

O navegador falhou durante a primeira tentativa em tela pequena, foi recuperado e a verificação concluída. Largura observada no conteúdo: 375 px, scrollWidth: 375 px. Também houve inspeção visual em tela maior. Essa revisão básica não representa certificação WCAG; revisão aprofundada e leitores de tela ficam na Fase 2.

Testes automatizados backend cobrem 401/403, privacidade, sessões, imutabilidade de publicações/execuções, revisões, auditoria, cálculos, filtros e importador. A CI prepara banco vazio e aplica migrations **antes** dos testes. O fluxo de navegador acima foi manual; não há suíte de regressão automatizada do navegador ainda.

## Repetir a verificação

Use um banco exclusivo de teste/demonstração; não use dados de produção. Instale dependências, gere segredo local, aplique migrations e inicie API e frontend conforme DEVELOPMENT. Cadastre uma conta fictícia, fonte por link e proposta com cada campo obrigatório; inclua financiamento explícito. Monte plano com a versão publicada, confira cálculo, publique, saia e consulte sem sessão. Edite/publice proposta v2 e confirme que plano v1 e histórico continuam iguais.

Verifique telas públicas sem dados, erros de publicação, acesso privado sem sessão e revisão de indicador com fonte. A conta administrativa de teste é configurada somente nesse banco, pelo comando descrito em INDICATORS.

## Redesign solicitado em 2026-10-06

Frontend com ESLint, TypeScript e build passando; links de documentação verificados. Nenhuma mudança de schema ou motor fiscal. A validação de navegador usa somente as contribuições fictícias do banco de demonstração.

| Grupo de telas | Larguras | Resultado |
| --- | --- | --- |
| Home, Brasil Atual, Meta Selic, propostas, planos, fontes, metodologia, transparência | 360, 768, 1280, 1920 | 32 combinações sem overflow da página |
| Painel, admin, minhas fontes, editor de proposta, editor de plano com simulação | 360, 768, 1280, 1920 | 20 combinações sem overflow da página |
| Entrar, cadastro, detalhe da proposta e detalhe do plano | 360, 768, 1280, 1920 | 16 combinações sem overflow da página |

No viewport de 360 px, clientWidth/scrollWidth do documento foram 345/345 (15 px do scrollbar). Nas outras larguras, 753/753, 1265/1265 e 1905/1905. Container desktop da home: 1440 px em viewport de 1920. Tabelas preservam sua rolagem interna.

- Contraste: varredura dos textos renderizados nas 12 telas públicas em ambos os temas, sem falhas de AA nos pares examinados; home com 113 elementos examinados por tema. Revisão das telas privadas também sem falhas nos pares examinados. Grandes títulos usam limiar 3:1; corpo e controles, 4,5:1. Avisos e texto de corpo têm no mínimo 16 px. Isso não é certificação completa de acessibilidade.
- Tema alternado por botão e restaurado após navegação/reload. Preferência guardada separadamente de autenticação. Regras de reduced-motion verificadas no código; não houve emulação da preferência no navegador.
- Sliders operados por teclado: estado inicial −20 bi; receita em 100, despesa em 60 e economia em 10: +50 bi; despesa em 100, receita em 90 e economia em 10: zero. Barra/avisos acompanharam valores fictícios.
- Menu mobile abriu com Enter, fechou com Escape e devolveu foco ao summary. Link “Ir para o conteúdo” focou MAIN/conteudo. Override de viewport removido após a revisão.
- Login/logout funcionaram com conta fictícia; acesso ao rascunho foi fechado após sair.
- Duplicar proposta gerou nova identidade e DRAFT v1, com valor 9999.99, referência e atribuição à proposta original v2.
- Duplicar plano manteve a proposta original v1; execução nova resultou em − R$ 1.234,56. Não herdou execução como resultado atual. Cópias revalidadas após carregar a versão completa somente na ação de duplicar.
- Original do plano continuou disponível sem login, com proposta v1 e saldo original. Nenhuma cópia foi publicada.

Não há suíte de regressão automatizada do navegador; continuam pendentes apoios/comentários, URL pública do repo, contato e validação do fluxo completo em Docker. Detalhes do sistema visual em [docs/design/DESIGN.md](../design/DESIGN.md).
Refinamento de performance: contagem reserva largura para o valor final e navbar reserva o espaço da conta antes da restauração da sessão; fontes usam fallback ajustado. Home e indicador rechecados nas 4 larguras (8 combinações adicionais), sem overflow. Ilustrações dos 3 passos também visíveis em 360 px. Não foi feito perfil formal de Web Vitals.


## Contextos — roteiro e execução DATA-05C, 2026-10-13

1. Sem sessão, abrir `/contextos`: somente publicações; buscar título de revisão privada não retorna esse rascunho. Abrir ID privado pela rota pública deve mostrar indisponibilidade genérica.
2. No painel do autor, criar/salvar contexto incompleto; observações são selecionadas com fonte/revisão/período, sem digitar números. Salvar exige ação explícita; navegação interna com texto pendente pede descarte e Escape conserva a edição.
3. Administrador distinto vê fila e preview sem poder editar/publicar por outro autor. Aceitação exige justificativa e quatro conferências; reabrir novo alvo zera essas declarações. Uma edição/confirmação antiga recebe 409, preservando o texto até descarte explícito.
4. Autor publica somente versão aceita; alterar depois cria nova revisão e requer nova conferência. A publicação anterior/histórico continuam públicos e imutáveis. Testes usam selo Exemplo fictício e nenhuma revisão automática de pesquisa real.
5. Conferir evidências recolhidas por clique/teclado: trecho se abre e recebe foco. No Brasil Atual, drawer e página de indicador oferecem contextos pertinentes; fechamento mantém comportamento/foco anterior.
6. 360/768/1280/1920, dois temas, campos legíveis, largura documental, pares de contraste e loading/vazio/erro/retry. Falha de API simulada apenas por pausa breve do processo local identificado, com retomada imediata.

Execução: fluxo fictício de revisão/publicação/edição, privacidade, confirmações, seletor e links conferidos; 16 configurações de editor/detalhe sem overflow, 13 pares AA. Integrações cobrem conflito/histórico/autoria/fontes sem contaminar demo. Conteúdo real em pesquisa está privado, sem revisão humana ou publicação; DATA-05C ainda Preparado. [Evidência](VERIFICATION.md) · [Pesquisa](../data/FIRST_CONTEXT_RESEARCH.md).
