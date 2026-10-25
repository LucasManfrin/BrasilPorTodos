# Segurança

Estado: desenvolvimento local; não há serviço público ou canal privado de segurança configurado.

Com a criação do remoto, habilitar reporte privado de vulnerabilidades no GitHub e atualizar este documento com o canal disponível. Não expor credenciais, tokens ou dados pessoais em issues públicas. Rotacionar credenciais comprometidas.

Auditoria local de autenticação/autorização e correções em 2026-10-25: [relatório](docs/governance/SECURITY_AUDIT.md). Não é certificação; pendências públicas de proxy, privilégios do banco, recuperação/proteção administrativa e operação permanecem abertas.

Critérios mínimos antes do lançamento: hash seguro de senha, expiração e revogação de sessão, proteção contra abuso de autenticação, autorização de autoria/admin no backend, privacidade de rascunhos, CORS explícito, validação de entrada, segredos fora do Git e ausência de busca de URLs arbitrárias.
