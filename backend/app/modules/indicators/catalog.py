"""Reviewed first series. Expand only after reviewing dataset, unit and reuse terms."""

BCB_SERIES = {
    "selic-meta": {
        "series": 432,
        "dataset": "432-taxa-de-juros---meta-selic-definida-pelo-copom",
        "name": "Meta Selic",
        "description": "Meta para a taxa Selic definida pelo Copom, em percentual ao ano.",
        "category": "ECONOMY",
        "unit": "% a.a.",
        "frequency": "DAILY",
        "scope": "Brasil; meta de política monetária",
        "methodology": (
            "SGS 432. Meta definida pelo Copom, distinta da taxa efetiva e de juros acumulados. "
            "Valores diários; não somar taxas ao longo do tempo."
        ),
    },
    "divida-bruta-pib": {
        "series": 13762,
        "dataset": (
            "13762-divida-bruta-do-governo-geral--pib---metodologia-utilizada-a-partir-de-2008"
        ),
        "name": "Dívida bruta do Governo Geral / PIB",
        "description": (
            "DBGG em percentual do PIB, segundo a metodologia do Banco Central "
            "utilizada a partir de 2008."
        ),
        "category": "FISCAL",
        "unit": "% do PIB",
        "frequency": "MONTHLY",
        "scope": "Governo Geral: Governo Federal, estados e municípios; conforme definição do BCB",
        "methodology": (
            "SGS 13762. Estoque de dívida bruta dividido pelo PIB de referência do BCB. "
            "Inclui operações compromissadas do BCB conforme o conceito oficial. "
            "Não confundir com dívida líquida ou apenas dívida federal. "
            "O dia 01 identifica o mês de referência, não uma medição diária."
        ),
    },
}
BCB_SERIES.update(
    {
        "divida-liquida-pib": {
            "series": 4513,
            "dataset": (
                "4513-divida-liquida-do-setor-publico--pib---total---setor-publico-consolidado"
            ),
            "name": "Dívida líquida / PIB",
            "description": "Endividamento líquido do setor público consolidado em relação ao PIB.",
            "category": "FISCAL",
            "unit": "% do PIB",
            "frequency": "MONTHLY",
            "scope": (
                "Setor público consolidado não financeiro e Banco Central, conforme "
                "definição do BCB"
            ),
            "methodology": (
                "SGS 4513. Dívida líquida desconta ativos conforme conceito oficial. "
                "Abrangência distinta da DBGG. O dia 01 identifica o mês; não somar "
                "estoques."
            ),
        },
        "atividade-ibc-br": {
            "series": 24363,
            "dataset": "24363-indice-de-atividade-economica-do-banco-central---ibc-br",
            "name": "Atividade econômica (IBC-Br)",
            "description": (
                "Indicador mensal de atividade econômica do Banco Central. Não equivale ao PIB."
            ),
            "category": "ECONOMY",
            "unit": "índice",
            "frequency": "MONTHLY",
            "scope": "Brasil; índice de atividade do BCB",
            "methodology": (
                "SGS 24363. Série sem ajuste sazonal. Comparações mês a mês podem refletir "
                "sazonalidade; preferir o mesmo mês do ano anterior. Não converter o índice "
                "em reais nem tratá-lo como PIB."
            ),
        },
    }
)
LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"
