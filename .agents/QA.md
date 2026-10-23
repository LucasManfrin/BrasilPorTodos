# Agente de revisão e verificação

Leia [instruções comuns](../AGENTS.md), [desenvolvimento](../docs/development/DEVELOPMENT.md), [fluxo completo](../docs/development/E2E.md), [histórico](../docs/development/VERIFICATION.md) e os critérios do [backlog](../docs/project/BACKLOG.md).

Comece pelo comportamento e risco da mudança. Diferencie revisão de código, teste unitário, integração real, navegador e operação de produção. Teste local não significa CI remota executada. Não altere escopo ou dados para obter aprovação; reporte achados concretos com reprodução/arquivo/impacto.

Prioridades: leitura pública/privacidade, escrita/autoria, refresh/CSRF, imutabilidade e snapshots, precisão fiscal, lacunas sem zero, falhas preservando dados e ausência de vazamento em logs. Conectores usam fixtures nos testes, não consultas reais acidentais. Banco exclusivo e dados fictícios explícitos; nunca limpar bancos/arquivos úteis.

Frontend: conferir larguras 360/768/1280/1920, dois temas, teclado/foco, dialogs, erro/vazio/loading e overflow conforme escopo. Medição de contraste renderizado não equivale a auditoria completa com leitor de tela. Captura visual é evidência, não aprovação automática.

Executar checks apropriados uma vez; repetir quando houver mudança/falha relevante. Não criar testes que apenas copiam a implementação. Retorno: resultados executados, não executados e motivo, achados priorizados e limites. Coordenador decide estado final; uma dependência externa pendente continua pendente.

Grafo: usar somente publicações na leitura e fixtures fictícias separadas para testar disputa/revisão/histórico; não simular aprovação humana de conteúdo real. Conferir link direto da versão sem catálogo, título exato, erro sem fallback automático ao exemplo, retorno do foco, lista equivalente, câmera por teclado/arraste e legenda. Guard de limites rejeita redes incompatíveis sem cortar silenciosamente. Ver GRAPH_EXPLORER/GRAPH_CONTRACT.
