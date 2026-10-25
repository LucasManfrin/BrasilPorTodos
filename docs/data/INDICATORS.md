# Indicadores e atualização

## Seleção verificada — onze séries em 2026-10-09

| Código | Origem | Unidade e referência |
| --- | --- | --- |
| selic-meta | BCB SGS 432 | % a.a., diária; meta, não rendimento acumulado |
| divida-bruta-pib | BCB SGS 13762 | % do PIB, mensal; Governo Geral, metodologia desde 2008 |
| divida-liquida-pib | BCB SGS 4513 | % do PIB, mensal; setor público consolidado |
| atividade-ibc-br | BCB SGS 24363 | Índice mensal sem ajuste sazonal; não é PIB em reais |
| ipca-mensal | IBGE SIDRA 1737 / variável 63 | % no mês; Brasil |
| ipca-12-meses | IBGE SIDRA 1737 / variável 2265 | % em 12 meses; não somar janelas sobrepostas |
| desocupacao | IBGE SIDRA 6381 / variável 4099 | % da força de trabalho de 14 anos ou mais; trimestre móvel encerrado no mês |
| rtn-receita-liquida | Tesouro RTN, tema 10 / série 10.01.2 | R$ nominais; mês, Governo Central; origem em R$ milhões |
| rtn-despesa-primaria | Tesouro RTN, tema 10 / série 10.03.1 | R$ nominais; mês, Governo Central; caixa, pagamento efetivo |
| rtn-resultado-primario | Tesouro RTN, tema 10 / série 10.04.1 | R$ nominais; mês; resultado primário acima da linha, positivo = superávit |
| pib-nominal-trimestral | IBGE SIDRA 1846 / variável 585 / classificação 11255, categoria 90707 | R$ correntes; trimestre, Brasil; PIB a preços de mercado; precisão original R$ 10.000 |

As sete primeiras séries foram verificadas na entrega de 2026-10-07; três séries RTN e o PIB nominal completam a expansão fiscal de 2026-10-09. A conta observada usa as três séries RTN, com um ano fechado comum; o PIB nacional do mesmo ano permite proporções sem alterar a abrangência do Governo Central. Contrato, fontes e limitações em [docs/data/FISCAL_BASELINE.md](FISCAL_BASELINE.md).

Definições e links específicos estão nos catálogos revisados do backend. [BCB dados abertos](https://dadosabertos.bcb.gov.br/) registra ODbL 1.0 para as séries usadas; preservar [termos ODbL](https://opendatacommons.org/licenses/odbl/1-0/). IBGE mantém o link dos [termos do portal](https://www.ibge.gov.br/acesso-informacao/acoes-e-programas/politica-de-privacidade.html); não atribuímos uma licença CC ou ODbL sem comprovação. MIT cobre apenas código/documentação autoral. Revisar os termos de uma eventual exportação consolidada antes do lançamento.

Nas séries mensais, o dia 01 representa o mês de referência, não uma observação diária. No PIB, o início do trimestre identifica a referência; os códigos SIDRA `YYYY01` a `YYYY04` são trimestres, não meses. Comparação de desemprego e IBC-Br usa o mesmo período do ano anterior; mudanças de taxas aparecem em pontos percentuais. Não atribuir melhora/piora nem causa automaticamente. Ver [roteiro de pesquisa](RESEARCH_BRIEF.md).

## Coletor diário

O serviço `indicator-collector` do Compose mantém a consulta diária às **00:00 em America/Sao_Paulo** (12:00 A.M.). Verifica a agenda no banco a cada minuto, sem chamar endpoints HTTP da aplicação. Ao iniciar, recupera uma consulta vencida; não reproduz cada dia perdido. Falha parcial permite nova tentativa após pelo menos uma hora do início anterior. Sucesso agenda a próxima meia-noite, evitando deslocar o horário por uma janela móvel de 24 horas. Consulta manual próxima do horário diário também respeita a proteção de uma hora. Reconsulta histórico de três anos para as séries mensais de contexto e um ano para Selic, em janelas de até 365 dias. As três séries RTN e o PIB nominal reconsultam cinco anos fechados e o ano em andamento; o PIB é trimestral e nunca é anualizado por extrapolação. Última divulgação pode ser anterior ao dia da consulta.

Na pasta backend, com ambiente/banco configurados e migrations aplicadas:

```sh
uv run python -m app.collect_indicators --username seu_admin
uv run python -m app.collect_indicators --username seu_admin --watch
```

Exige administrador ativo já configurado; não cria conta nem promove ninguém. `--username` ou `COLLECTION_USERNAME` seleciona a atribuição; sem seleção, usa o primeiro ADMIN ativo por criação/ID. Sem ADMIN, registra adiamento sem expor identidade e tenta novamente enquanto o worker estiver ativo. Para instalação nova, cadastrar a própria conta e usar `uv run python -m app.manage bootstrap-admin --username seu_usuario --reason "Responsável local"`, que recusa se já existe administrador. `--now` é uma opção explícita de operador para reprocessar após reparo; o botão da interface não ignora o limite.

O Compose inicia e reinicia o worker com `restart: unless-stopped`; Docker Desktop e computador precisam estar ligados. Não instala tarefa do Windows nem automação do Codex. Para execução nativa, inicie explicitamente `--watch` e configure `COLLECTION_SCHEDULE_ENABLED=true` para anunciar o agendamento na API; a flag informa a configuração, não comprova que o processo está vivo. O horário/fuso/retentativa são configuráveis em `COLLECTION_DAILY_AT`, `COLLECTION_TIMEZONE` e `COLLECTION_RETRY_MINUTES` (mínimo 60). No Compose esses valores estão declarados no ambiente compartilhado em `compose.yaml`, que prevalece sobre `backend/.env`. A operação pública ainda exige supervisão e alertas. Não há consultas ao BCB, IBGE ou Tesouro a cada visita.

## API, integridade e falhas

- GET `/api/v1/indicators`, detalhe `/{code}`: leitura pública, série cronológica e histórico de revisões paginado.
- GET `/api/v1/indicators/collection/status`: última execução, resultado por série e agenda configurada/próxima tentativa. Não é prova de vida do worker. Timestamps são UTC na API e apresentados em São Paulo na interface; referência mensal/anual do indicador mantém seu próprio calendário.
- GET `/api/v1/indicators/baseline/current`: indicadores de contexto e objeto fiscal separado, com fontes, referências, hash e limitações.
- GET `/api/v1/indicators/baseline/fiscal`: base primária observada, ano fechado comum, meses e revisões; PIB anual formado por quatro trimestres e proporções quando disponíveis. Não é previsão nem soma automática das propostas.
- POST `/api/v1/admin/indicators/collect`: administrador autenticado; agenda em segundo plano e respeita intervalo de uma hora. A interface acompanha o estado; visitantes podem apenas recarregar dados salvos.

Lock consultivo PostgreSQL impede coleta concorrente mesmo entre processos. Execuções e falhas ficam registradas. Falha externa preserva observações anteriores; não substitui ausência por zero. Timeout, tamanho de resposta descomprimida, domínio HTTPS e redirecionamento são limitados. Apenas URLs construídas pelos conectores revisados são consultadas; URLs contribuídas continuam referências sem fetch/upload.

Observações são append-only: mesmo valor, fonte e proveniência semântica não duplica revisão; mudanças criam nova revisão. A proveniência inclui o conjunto compatível: os três componentes do mês no RTN e os quatro trimestres do ano no PIB. Mudar um componente pode alterar a impressão digital e gerar revisão dos demais valores inalterados daquele conjunto, preservando sua coerência. Datas de consulta e intervalos diferentes na URL, sozinhos, não criam uma revisão falsa. Payload fora de período, futuro, duplicado, não finito ou fora da unidade/abrangência esperada é recusado.

Administração permite manter definições e acrescentar observações com auditoria. Mudança de unidade, abrangência ou método de uma série já observada exige outra identidade. Conteúdo fictício tem marca explícita e não aparece em produção.

## Integridade dos conjuntos fiscais

As três séries RTN são buscadas e validadas antes de qualquer gravação do conjunto, em uma única transação. O PIB usa outro conjunto, também atômico e independente: uma indisponibilidade do IBGE não invalida a base absoluta já disponível do Tesouro. A montagem anual exige doze meses compatíveis nas três séries RTN e, para proporções, exatamente quatro trimestres do mesmo ano no PIB.

O conector RTN lê números JSON com Decimal, converte milhões para reais e arredonda aos centavos com half-even. A identidade mensal aceita diferença máxima de R$ 0,03; a diferença anual também é informada, sem alterar números para forçar igualdade. O valor publicado e o resultado calculado por receita menos despesa permanecem distintos.

O conector de PIB solicita duas casas decimais em milhões, em URL fixa da API SIDRA, e valida Brasil, variável, categoria e unidade. A precisão da fonte é R$ 10.000. O total anual é a soma revisável dos quatro trimestres das CNT, não a série anual definitiva do SCN. Sem denominador anual compatível, os percentuais ficam ausentes; o saldo fiscal absoluto continua disponível. Proporções são apresentadas com quatro casas decimais.

Fontes privadas com a mesma URL de uma origem oficial não podem ser promovidas silenciosamente nem expor rascunhos. Os coletores mantêm fontes oficiais identificadas e preservam os contratos de visibilidade. A tarefa DATA-06 trata compatibilidade de ente, regime e período dos impactos antes de qualquer cenário que combine propostas com esta referência.

## Ampliação de emprego — 2026-10-10

Catálogo atual: 14 séries. Acrescentadas PNAD SIDRA 6390/5933 (renda real habitual, Reais → R$), 8513/12466 (informalidade, %) e 5944/4096 (participação, %). Divulgação mensal, Brasil, trimestre móvel; 35 observações reais por série. Definições, população, termos e verificação em [docs/data/EMPLOYMENT_INDICATORS.md](EMPLOYMENT_INDICATORS.md).

Renda reconsultada em conjunto coerente, incluindo todo o histórico já salvo. Âncora global conferida antes/depois; lote validado e gravado atomicamente. Proveniência registra a base de preços inferida da metodologia oficial e última referência publicada. Rebase gera revisão sem alterar publicações. Taxas seguem o coletor autorizado/idempotente. Fontes reconhece as novas identidades sem mudar sua tela.

Na coleta de 10/10/2026, as três novas séries tiveram SUCCESS; IBC-Br e dívida líquida falharam por HTTP e preservaram dados anteriores. Visitas e “Recarregar” leem o cache; o botão não dispara consultas externas por visitante.

## Séries auxiliares de composição — DATA-07A

Dez séries adicionais do RTN detalham receita total/transferências e filhos diretos da receita/despesa, com catálogo/fingerprint/coleta separados. Permanecem fora do catálogo público principal e de baseline/current, mas disponíveis para manutenção administrativa e detalhe por código. O endpoint `GET /api/v1/indicators/baseline/composition` usa o mesmo ano da referência fiscal. A rotina diária registra o grupo `rtn-composition`, sem consultas por visitante. [Contrato](FISCAL_COMPOSITION.md).

Coleta real de 2026-10-11: 120 observações de 2025, idempotentes, revisão máxima 1; 14 indicadores e composição terminaram com sucesso. Isso não encerra o catálogo mínimo F1-03 nem amplia o recorte a funções/juros/outros entes.

## Séries auxiliares de juros — DATA-07B1

Três séries adicionais, grupo `rtn-interest`, endpoint `GET /api/v1/indicators/baseline/interest`; ano fechado da referência atual, catálogo/fingerprint próprios, fora dos 14 indicadores principais e de baseline/current. Nominal usa primário abaixo da linha e juros por competência. [Contrato](FISCAL_INTEREST.md). Entrega local verificada em 2026-10-11: 36 observações reais de 2025, repetição sem duplicação/revisão extra; conjunto AVAILABLE e coleta completa SUCCESS. 503 testes backend/157 frontend e checks/build passaram. Não incorporar ao cálculo incremental nem alterar publicações.


## Execução federal por função — DATA-07B2

Grupo diário `federal-spending`, endpoint `GET /api/v1/indicators/spending/functions`. Agregados em `fiscal_spending_cohorts`, não novas séries fictícias em IndicatorValue. Revisão indivisível por arquivo/ano/versões, três naturezas e estágios, meses/linhas observados e rótulos originais. Leitura pública do ano fechado da referência atual, sem misturar critério funcional ao RTN. [Contrato e verificação](FISCAL_SPENDING.md). Fonte ligada à revisão pública recebe licença e marcador de coleta verificados; URL igual sozinha não prova coleta.


## Governo Geral por esfera — DATA-07B3

Grupo diário `general-government`, endpoint público `GET /api/v1/indicators/government/general`, revisões anuais próprias em `general_government_cohorts` (migration 0012). Ano fechado da referência atual; oito grupos/métricas, competência modificada e consolidação da STN, cobertura municipal estimada explícita. Não cria IndicatorValue fictício nem muda os 14 indicadores principais, as treze séries auxiliares ou a base contextual. Coleta real 2025 e preservação verificadas em 2026-10-12. [Contrato](GENERAL_GOVERNMENT.md).

Consultas leem revisão salva; falha conserva história e estado público limitado. Download estritamente oficial e limitado, verificação dupla do arquivo/publicação, parser/precisão versionados. Fonte só recebe marcador `general-government` por vínculo real com revisão validada; licença/atribuição da EFGG são os termos Tesouro Transparente. Fonte privada com URL igual não é promovida.
