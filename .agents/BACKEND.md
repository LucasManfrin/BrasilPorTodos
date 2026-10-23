# Agente backend

Leia [instruções comuns](../AGENTS.md), [arquitetura](../docs/architecture/ARCHITECTURE.md), [modelo](../docs/architecture/DATA_MODEL.md), [auth](../docs/architecture/AUTHENTICATION.md) e [desenvolvimento](../docs/development/DEVELOPMENT.md).

Escopo: FastAPI, Pydantic, SQLAlchemy, Alembic, serviços/transações e testes. Router valida HTTP; service aplica domínio/autoria/transação; persistência nos módulos. Motor fiscal permanece puro e independente de HTTP/banco. Não criar repository ou camadas sem necessidade.

Leitura pública apenas do permitido; escrita autenticada/autorizada; fontes/rótulos privados não vazam por URL coincidente. Rascunhos próprios, snapshots e composição publicados imutáveis inclusive para admin. Atualização explícita de rascunho não reescreve publicação. Simulações preservam entrada/hash/versão/resultado, sem substituir execução anterior.

Money Decimal/NUMERIC, timestamp UTC, valores string na API. Prefixo/envelope/paginação/erros seguem contratos existentes. Não registrar tokens/senhas/payloads privados. Preserve revogação, refresh/CSRF, origem explícita e limites; não desabilitar proteção para fazer um teste passar.

Migrations revisadas, sem create_all no startup. Integração em banco exclusivo; não rodar downgrade destrutivo em dados úteis. Testes devem cobrir regra, autorização, publicação, revisão e falha/rollback. Ruff/check de formatação e pytest pertinentes; Alembic check com banco quando afetar modelos/schema. Alteração de API exige coordenação de frontend. Dados/finanças exigem o guia FISCAL; coletor não busca URLs arbitrárias.


Contextos/evidências: [CONTEXT_EVIDENCE](../docs/data/CONTEXT_EVIDENCE.md). Biblioteca DATA-05A valida estrutura/hash/registro declarado. Serviço DATA-05B implementa API/modelos, não aceita revisor/aprovação de cliente como autorização, resolve IDs/metadados e visibilidade e preserva revisões/publicações; testes de acesso/rollback/cópias permanecem obrigatórios. Não incorporar contextos nos snapshots legados automaticamente.


Atualização DATA-05B: persistência/API/migration 0013 entregues; contrato vigente em CONTEXT_EVIDENCE. Autor-only escreve/publica, outro admin ativo revisa. IDs oficiais/definições congeladas/termos/cobertura resolvidos pelo servidor, referências rechecadas sem atualização silenciosa. `REVIEW_MATCHES` da biblioteca segue sem autorização por si; usar serviço/gates reais. Interface e primeiros contextos reais permanecem C.


GRAPH-01A: [GRAPH_CONTRACT](../docs/data/GRAPH_CONTRACT.md) define biblioteca pura de nós/arestas/snapshots/revisão declarada/topologia. Ler antes de trabalhar nos grafos. Nenhum resultado MATCHES autoriza publicação; B resolve identidades/fontes e aplica autorização/transação no serviço. Fonte histórica é fotografia por aresta, enquanto nó id/revisão exige conteúdo exato. Sem magnitude/coeficiente ou integração fiscal/IA nesta fatia. DATA-05C tem interface e pesquisa privada; revisão humana real continua pendente.

GRAPH-01B implementado: resolver/service/router e nove tabelas append-only/migration 0014. Autor escreve/publica; outro admin revisa. Última decisão/checklist/hash/revisão e referências atuais governam publicação explícita REVIEWED/DISPUTED; rejeição não publica. Conjunto só reutiliza versões públicas e preserva fotografias. Leituras de listas/histórico são resumidas por projeção; detalhes completos. Nó público exige testemunha da versão exata; conjunto real não usa testemunha de exemplo. Ler contrato vigente antes de implementar C (página explicativa/explorador/lista); motor, magnitudes, IA e contexto real continuam separados.
