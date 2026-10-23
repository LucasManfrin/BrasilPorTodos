# Juros e resultado nominal do Governo Central

## Recorte observado separado

DATA-07B1 acompanha três fluxos mensais do Governo Central em um mesmo ano fechado: primário **abaixo da linha**, juros nominais assinados e resultado nominal. São estatísticas apuradas pelo Banco Central e republicadas pela Secretaria do Tesouro Nacional no [RTN](https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional), com licença [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Não é todo o setor público, execução orçamentária por função ou uma projeção.

| Papel | Série, tema 10 | Critério |
| --- | --- | --- |
| Resultado primário abaixo da linha | `10.07.1` | Caixa, com os tratamentos metodológicos do BCB |
| Juros nominais assinados | `10.08.1` | Juros líquidos apropriados por competência |
| Resultado nominal | `10.09.1` | Combinação de primário e juros, regime misto |

A identidade nesta convenção de sinais é `primário abaixo da linha + juros assinados = resultado nominal`. Juros negativos reduzem o saldo; não subtrair novamente nem impor que todo mês histórico seja negativo. Estes juros não são amortização, despesa orçamentária paga ou Selic multiplicada pelo estoque da dívida.

O [Manual RTN 2026](https://cdn.tesouro.gov.br/sistemas-internos/apex/producao/sistemas/thot/arquivos/publicacoes/28153_894487/Manual%20Externo%20RTN%20VF.pdf), páginas 9–13, e o [manual fiscal do BCB](https://www.bcb.gov.br/content/estatisticas/notas_metodologicas/estatisticas-fiscais/estatisticasfiscais.pdf), páginas 32–39, fundamentam abrangência e critérios. O primário acima da linha da [referência fiscal](FISCAL_BASELINE.md) tem outra apuração: não substituí-lo nesta identidade. A diferença entre métodos não é residual de arredondamento e não se resolve mudando os números.

## Unidade e conferência

A API retorna milhões de reais correntes. Ler como Decimal, multiplicar por 1.000.000 e arredondar cada observação a centavos com half-even; somar os doze meses. Centavos da representação não aumentam a precisão econômica da fonte. Valores finitos e dentro de NUMERIC são obrigatórios.

Conferir a identidade por mês, tolerância máxima R$ 0,03; divulgar o residual anual efetivo, sem ajustar valores. Pesquisa de 2026-10-11 conferiu 36 pares API/planilha oficial de 2025, iguais após conversão. Totais observados revisáveis: primário abaixo da linha −R$ 58.687.099.866,91; juros −R$ 891.879.890.155,13; nominal −R$ 950.566.990.022,04. Residual mensal/anual zero. A diferença abaixo menos acima da linha é R$ 3.007.209.114,08, de caráter metodológico; nenhuma ponte de ajustes foi inferida.

## Coleta, leitura e proteção das versões

Catálogo auxiliar de três séries, impressão digital própria, doze meses e revisões coerentes. Gravação atômica; lacuna, alteração de definição/fonte, fingerprint inconsistente ou identidade fora da tolerância impedem disponibilidade. Falha conserva o lote salvo; ausência nunca vira zero. As séries permanecem fora do catálogo principal e de `baseline/current`, mas disponíveis na administração.

Endpoint público `GET /api/v1/indicators/baseline/interest`. Usa o ano fechado da referência corrente, sem comparar os montantes dos dois primários nem substituir a referência. Contrato explicita `accounting_basis=mixed`, `methodology_basis=below_line`, `component_bases={primary:cash,interest:accrual}`, BRL nominal, fonte/atribuição, meses, coleta, método e reconciliação.

Painel expansível em Brasil Atual confere ano, ente, período, critérios, doze meses e identidade com BigInt antes de mostrar valores; inclui números compactos/exatos, fonte e limites. Consultas públicas leem dados salvos. Rotina diária registra `rtn-interest`, com lock/cooldown e idempotência existentes; consultas ao Tesouro não são disparadas por visitantes. Operação persistente de produção continua pendente.

Esta camada não é incorporada ao motor incremental, aos cenários declarados nem aos snapshots/contextos de propostas e planos. Conjuntos primário e composição conservam fingerprints e contratos. Gasto por função e outros entes continuam no DATA-07B; [contrato de pesquisa](FEDERAL_SPENDING_RESEARCH.md).

## Entrega local verificada — 2026-10-11

36 observações reais idempotentes, doze meses e residual zero; API/painel AVAILABLE, contexto e publicações preservados. 503 testes backend/157 frontend, checks/build e oito combinações de largura/tema passaram. [Evidência](../development/VERIFICATION.md). DATA-07B1 concluído; B2/B3 permanecem pendentes.
