# Agente fiscal e de dados oficiais

Leia [instruções comuns](../AGENTS.md), [metodologia](../docs/data/METHODOLOGY.md), [indicadores](../docs/data/INDICATORS.md), [base fiscal](../docs/data/FISCAL_BASELINE.md) e [PNAD](../docs/data/EMPLOYMENT_INDICATORS.md) quando pertinente.

Escopo: `backend/app/integrations`, módulo indicators, cálculo puro e contratos de fontes/dados; interface apenas em coordenação com frontend. Integrações concretas: BCB SGS, IBGE SIDRA e Tesouro RTN. Usar documentação e metadados oficiais, sem IDs ou valores de memória.

Antes de incorporar uma série, registrar instituição, tabela/série/variável/classificação, unidade original/final, população/denominador, frequência, território/ente, critério contábil, preços reais/nominais/data-base, referência, divulgação/coleta, transformações, precisão e termos de uso. Não assumir licença por analogia. URLs contribuídas não autorizam busca arbitrária.

Use Decimal/NUMERIC e revisões idempotentes com proveniência. Mantenha cliente HTTP limitado, hosts revisados, timeouts/tamanho e recortes validados. Ausência não é zero. Conjuntos fiscais/PIB/renda precisam de coerência, transação/rollback e preservação após falha. Renda real deve reconsultar todo o histórico salvo na mesma base; não virar receita fiscal. Precisão original deve aparecer, sem centavos fictícios.

Base observada usa ano fechado e ente/critério compatíveis; PIB nominal do mesmo ano para proporções. Não anualizar mês parcial nem usar IBC-Br como PIB. Impactos incrementais não se somam automaticamente à base; DATA-06 exige contratos e premissas. Financiamento declarado não duplica receita/economia. Grafo/IA não geram coeficiente ou resultado fiscal por si.

Verificar contratos unitários e integração PostgreSQL pertinente: unidades/escala/limites, lacunas, idempotência/revisão, mudança de base, rollback, privacidade de fontes e snapshots publicados. Retornar fontes oficiais e evidência de coleta separadas de teste; coordenar documentação/backlog com DOCS.

Para impactos/execuções, ler [FISCAL_COMPATIBILITY](../docs/data/FISCAL_COMPATIBILITY.md). Comparar com a referência congelada, preservar o legado, não inferir metadados ausentes; preços constantes exigem ano-base. Compatibilidade histórica não autoriza projeção nem valida custo/causalidade.

Cenários futuros: ler [FISCAL_SCENARIOS](../docs/data/FISCAL_SCENARIOS.md). Biblioteca e integração DATA-06B1/06B2 disponíveis e verificadas no recorte documentado. Não confundir compatibilidade com cenário declarado e com ano observado; não repetir base, misturar recortes ou tratar confirmação de exclusão como detector de sobreposição.

Composição: ler [FISCAL_COMPOSITION](../docs/data/FISCAL_COMPOSITION.md). Preservar trio RTN/fingerprint v1 e base contextual; catálogo auxiliar/endpoint separados. Filhos diretos, sinais publicados, transferências uma vez; revisar âncoras e reconciliação antes de disponibilizar. Juros/nominal foram separados no DATA-07B1; funções e outros entes continuam B2/B3.

Juros/nominal: ler [FISCAL_INTEREST](../docs/data/FISCAL_INTEREST.md). Manter abaixo da linha e regime misto explícito; sinais publicados, catálogo/fingerprint auxiliares, sem trocar o primário acima da linha. Gasto funcional: [pesquisa](../docs/data/FEDERAL_SPENDING_RESEARCH.md), natureza/estágio e rótulos sem classificação preservados, sem inferir ponte para RTN.

Gasto funcional: [FISCAL_SPENDING](../docs/data/FISCAL_SPENDING.md) é o contrato de integração; [pesquisa original](../docs/data/FEDERAL_SPENDING_RESEARCH.md) conserva evidência. Conjunto completo append-only e critérios próprios, sem sentinela com zero inventado ou incorporação ao RTN/motor.


Outros governos: ler [GENERAL_GOVERNMENT](../docs/data/GENERAL_GOVERNMENT.md), [SICONFI](../docs/data/SICONFI_RESEARCH.md) e [NFSP](../docs/data/PUBLIC_SECTOR_RESEARCH.md). EFGG anual/competência modificada e cobertura extrapolada são próprios; usar ajustes de consolidação publicados, nunca fabricar soma nacional de declarações. Termos/atribuição STN não são ODbL por analogia. Conjunto imutável auxiliar, sem alterar motor/base congelada.


Contextos: ler [CONTEXT_EVIDENCE](../docs/data/CONTEXT_EVIDENCE.md). DATA-05A é somente biblioteca pura; REVIEW_MATCHES não é autorização nem prova de causalidade. DATA-05B deve resolver referências reais e privacidade/autoria, atribuir revisão pela camada confiável e preservar publicação. Contrapartidas ausentes continuam ausentes; não produzir coeficientes, probabilidades ou previsões a partir de textos/evidências.


Atualização DATA-05B: persistência/API/migration 0013 entregues; contrato vigente em CONTEXT_EVIDENCE. Autor-only escreve/publica, outro admin ativo revisa. IDs oficiais/definições congeladas/termos/cobertura resolvidos pelo servidor, referências rechecadas sem atualização silenciosa. `REVIEW_MATCHES` da biblioteca segue sem autorização por si; usar serviço/gates reais. Interface e primeiros contextos reais permanecem C.


GRAPH-01A: [GRAPH_CONTRACT](../docs/data/GRAPH_CONTRACT.md) define biblioteca pura de nós/arestas/snapshots/revisão declarada/topologia. Ler antes de trabalhar nos grafos. Nenhum resultado MATCHES autoriza publicação; B resolve identidades/fontes e aplica autorização/transação no serviço. Fonte histórica é fotografia por aresta, enquanto nó id/revisão exige conteúdo exato. Sem magnitude/coeficiente ou integração fiscal/IA nesta fatia. DATA-05C tem interface e pesquisa privada; revisão humana real continua pendente.

GRAPH-01B implementado: resolver/service/router e nove tabelas append-only/migration 0014. Autor escreve/publica; outro admin revisa. Última decisão/checklist/hash/revisão e referências atuais governam publicação explícita REVIEWED/DISPUTED; rejeição não publica. Conjunto só reutiliza versões públicas e preserva fotografias. Leituras de listas/histórico são resumidas por projeção; detalhes completos. Nó público exige testemunha da versão exata; conjunto real não usa testemunha de exemplo. Ler contrato vigente antes de implementar C (página explicativa/explorador/lista); motor, magnitudes, IA e contexto real continuam separados.
