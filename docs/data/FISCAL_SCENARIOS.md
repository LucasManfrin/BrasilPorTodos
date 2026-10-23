# Cenário fiscal futuro declarado

DATA-06B1/06B2 implementados: motor puro e cenário opcional nos planos, com persistência, revisão humana e leitura pública. [Compatibilidade histórica](FISCAL_COMPATIBILITY.md) · [Metodologia](METHODOLOGY.md) · [Backlog](../project/BACKLOG.md).

## Problema e alcance

Uma referência de ano fechado não pode ser repetida automaticamente nos anos seguintes. Para examinar propostas futuras, precisamos distinguir o observado de uma trajetória com premissas explícitas. A primeira versão do contrato aceita valores anuais declarados: não calcula inflação, PIB ou arrecadação futura por conta própria.

Restrito a Governo Central, BRL nominal, caixa, componentes primários e ano inteiro. Não inclui juros, resultado nominal, estados/municípios, preços constantes, conversão de regime ou causalidade. Outros recortes continuam sem combinação automática.

## Entradas

- Snapshot contextual com identificador e referência fiscal histórica validada pelo mesmo contrato RTN de DATA-06A. A base é contexto/origem preservada, não a receita/despesa futura.
- Cenário com identificador, título, explicação, identificador da base de referência, início/fim e declaração sobre exclusão dos impactos das propostas.
- Uma linha por ano com receita primária líquida, despesa primária e justificativa das premissas. Fontes HTTP/HTTPS podem ser informadas; o motor não faz consultas externas.
- Versões de propostas com estado de estimativa, habilitação e parcelas anuais, preservando os metadados de DATA-06A.

Todos os anos precisam ser posteriores ao ano observado. Horizonte de até 30 anos consecutivos, limitado também a 1900–2200. Limite técnico, não promessa de capacidade preditiva nesse prazo. Ano faltante ou repetido é erro; não preencher com zero. Zero informado é aceito. Money exige Decimal finito, não negativo, máximo NUMERIC(18,2) e centavos; float/bool e valores inválidos são recusados. O identificador da base deve corresponder ao snapshot recebido.

## Compatibilidade com o cenário

O contrato histórico DATA-06A permanece inalterado: uma parcela futura não passa a ser comparável com um ano observado. Este módulo adicional compara parcelas habilitadas/dentro do horizonte com o recorte do cenário e o próprio ano anual declarado. Mesmo ano futuro e metadados completos do recorte restrito permitem a comparação **com o cenário**, não com o dado observado.

Ausência de metadados, outro ente, competência, juros, preços constantes ou ano parcial bloqueiam combinação com motivos por parcela. NOT_ESTIMATED ativo bloqueia o resultado conjunto; não é zero. NOT_APPLICABLE não fabrica parcelas. Propostas desativadas e valores fora do horizonte conservam o tratamento/avisos do motor incremental existente.

## Dupla contagem e combinação

O autor deve declarar que os valores do cenário excluem os efeitos das medidas selecionadas. Sem essa confirmação, registrar DOUBLE_COUNTING_UNCHECKED e não combinar. Na integração, vincular essa declaração à composição/premissas preservadas e exigir nova revisão quando mudarem. Essa declaração não detecta sobreposição semântica entre propostas; é uma premissa humana que deve ser revista e preservada.

```text
receita com medidas = receita declarada + novas receitas − reduções de receita
despesa com medidas = despesa declarada + novas despesas − economias
resultado primário com medidas = receita com medidas − despesa com medidas
```

Se alguma parcela for incompatível/incompleta, alguma medida ativa não tiver estimativa, a declaração de exclusão faltar ou algum componente calculado ficar negativo/exceder NUMERIC(18,2), bloquear combinação em todo o horizonte. Valores combinados acima do limite recebem PROJECTED_AMOUNT_OVERFLOW. Não descartar silenciosamente a parcela problemática nem limitar componente a zero; o somatório incremental exato continua separado, mesmo quando não cabe nesse limite. Exibir premissas anuais e somatório incremental separados, com avisos e natureza declarada da soma.

Sem parcelas avaliáveis, exibir cenário sozinho como NO_IMPACTS, sem alegar que as medidas foram aplicadas. Cumulativo é apenas a soma incremental do período, não “orçamento disponível” por agregar receitas de vários anos.

## Saída e versões

Resultado por ano distingue cenário declarado, efeitos incrementais e resultado conjunto opcional. Estado e motivos identificam o que impediu combinação. Método de cenário tem versão própria 1.0.0; agregação reutiliza motor 1.0.0 existente. Entradas não são alteradas pelo cálculo.

Resultado conjunto, mesmo compatível, é uma simulação condicionada a estimativas e premissas, não previsão oficial nem validação do custo ou das causas. O módulo não produz indicadores sociais, dívida ou PIB, nem transforma grafo/IA em coeficientes.

## Integração aos planos — DATA-06B2

Implementada na migration 0010 e nos serviços/API/interface dos planos. Premissas e revisão pertencem à versão e à execução preservadas; nada é acrescentado retroativamente às publicações antigas. Ausência de cenário mantém o comportamento incremental.

## Biblioteca implementada e verificação — 2026-10-10

[scenario.py](../../backend/app/simulation/scenario.py) expõe simulate_scenario(baseline_snapshot, scenario, policies). FiscalScenario e ScenarioYear representam as premissas; ScenarioPolicy/ScenarioImpact representam as versões/parcelas. Dataclasses imutáveis e tuplas, Decimal, sem HTTP/banco/IA. ScenarioResult distingue declared, incremental e combined por ano, assessments/issues/warnings, recortes da soma, acumulado incremental e versões dos métodos.

87 testes específicos passaram; suíte unitária backend completa com 282 testes passou, além de Ruff/formatação. Identidade de componentes, precisão, limite, ausência, incompatibilidade, dupla contagem, referências/anos, inputs inválidos, exclusões e imutabilidade cobertos. Este registro descreve a entrega isolada DATA-06B1. A integração posterior DATA-06B2 está descrita abaixo.

## Contrato de integração DATA-06B2 — 2026-10-10

Implementado e verificado localmente. Cenário opcional no plano; ausência mantém o cálculo incremental atual. Uma coluna nullable fiscal_scenario na PlanVersion preserva premissas por versão. Não preencher planos/execuções antigos retroativamente. O cenário não obriga reformular a criação de propostas.

Rascunho aceita campos ainda incompletos e valores anuais null. Confirmar/simular/publicar cenário ativo exige configuração válida: referência correspondente, anos posteriores à base e alinhados ao horizonte do plano, uma linha por ano, valores/justificativas explícitos. Dados ausentes não viram zero; configuração inválida gera erro claro, sem mudar silenciosamente para modo incremental.

### HTTP e representação

PlanInput/PlanUpdate acrescentam fiscal_scenario opcional; PATCH null remove. Campos autorais: title, explanation, reference_baseline_id e years com year, net_revenue, primary_expenditure, justification e source_urls. Dinheiro string decimal ou null no rascunho; URLs válidas sem credenciais, sem consultas externas. Os recortes restritos do motor não são opções de conversão.

PlanVersion expõe também campos readonly: excludes_plan_impacts, review_input_hash, reviewed_input_hash e reviewed_at. Cliente não escreve esses campos por PATCH. O endpoint POST /api/v1/plans/{id}/fiscal-scenario/confirm recebe expected_input_hash, exige autoria/sessão, apenas rascunho e estado atual correspondente. Estado alterado retorna SCENARIO_CHANGED; configuração incompleta não pode ser confirmada.

O hash de revisão vincula snapshot contextual completo, horizonte, premissas normalizadas e composição ordenada (versões, ativação e posição). Editar esses dados desfaz a confirmação; repetir um salvamento idêntico ou editar somente título/resumo/visão do plano a preserva. Criar novo rascunho/duplicar conserva premissas, mas exige nova confirmação. Referência antiga permanece explícita se o novo rascunho adotar outra base, sem reatribuir automaticamente sua origem.

### Execução e leitura

Execução com cenário guarda entrada/revisão/versão do método no input_snapshot.fiscal_scenario e resultado completo em assumptions.fiscal_scenario, com valores decimais serializados como strings. Entradas participam do hash; resultado acompanha a execução imutável. O resultado anual incremental existente continua separado, assim como a avaliação histórica: compatibilidade com premissas futuras não equivale a compatibilidade com ano observado.

Confirmação significa que o autor revisou a exclusão dos efeitos nas premissas, não que custos ou relações causais foram validados. Parcelas incompatíveis ou sem estimativa podem produzir resultado conjunto bloqueado e publicado com motivos, cenário declarado e incremental separados; combined=null não vira saldo zero. Sem cenário ativo, não acrescentar chaves vazias a snapshots/assumptions novos nem reescrever os antigos.

### Interface

Editor de plano mantém o modo incremental como padrão e oferece comparação com cenário futuro como opção. Premissas anuais não recebem valores históricos nem crescimento automático. Ajustar anos/adotar nova referência é ação explícita; valores retidos permanecem, confirmação precisa de nova revisão. O botão de revisão salva o estado atual antes de confirmar o hash recebido do servidor.

Leitura pública distingue cenário declarado, efeitos incrementais e receita/despesa/resultado com medidas por ano. Exibe justificativas, URLs e limites preservados; quando bloqueado, mostra razões e valores separados. Valores exatos acessíveis, layout com tokens existentes e estados de erro/busy. Home, Brasil Atual, Fontes e editor de propostas permanecem fora desta alteração.


## Verificação da integração — 2026-10-10

426 testes backend com PostgreSQL de integração e 116 testes frontend passaram; Ruff/formatação (114 arquivos), ESLint, TypeScript e build final passaram. Migration 0010 revertida/reaplicada no banco de integração e Alembic sem drift; links locais verificados.

32 combinações em 360/768/1280/1920 e temas claro/escuro: editor de cenário, resultado público com premissas abertas, campos de metadados da proposta e resultado legado, sem overflow da página. Tabelas têm rolagem interna no celular. Salvamento/reabertura, configuração incompleta, bloqueio sem revisão, combinação confirmada, revogação por composição, cópia sem confirmação e leitura anônima conferidos. Ano-base obrigatório em preços constantes e removido em nominal; foco por teclado visível. Nenhum erro de console na conferência final. Auditoria aprofundada de acessibilidade permanece F2-01.

Backup e checkpoint local confirmaram publicações/execuções anteriores intactas. Migration 0010 revertida/reaplicada somente no banco de integração; ambiente demonstrativo atualizado de forma aditiva. Exemplos novos explicitamente fictícios e restritos a development.
