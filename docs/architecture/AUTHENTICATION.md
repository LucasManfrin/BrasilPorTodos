# Contas e sessões

Backend e interface implementados em F1-02/F1-10. O token de acesso fica em memória; renovação coordena uma requisição por vez. O proxy Next.js preserva os dois cookies e cabeçalhos de sessão sob a mesma origem.

Auditoria local de 2026-10-25 e limites de criptografia/operação em [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md). Correções de sessão/configuração aplicadas; F2-02 mantém pendências públicas, sem certificação de segurança.

## Contrato

| Endpoint | Entrada / autorização | Resultado |
| --- | --- | --- |
| POST /api/v1/auth/register | JSON: name, username, email, password | Conta USER, sessão e access token; 201 |
| POST /api/v1/auth/login | JSON: email, password | Sessão e access token |
| GET /api/v1/auth/me | Authorization: Bearer access_token | Dados privados da própria conta |
| POST /api/v1/auth/refresh | Cookie de refresh e X-CSRF-Token | Novo access token e rotação do refresh/CSRF |
| POST /api/v1/auth/logout | Cookie de refresh e X-CSRF-Token | Revogação imediata da sessão e remoção de cookies |

Respostas usam `data`; erros usam `error.code` e `error.message`. Respostas de sessão não podem ser cacheadas. Nenhum endpoint retorna hash de senha ou permite escolher o papel ADMIN no cadastro.

## Transporte e revogação

JWT HS256 de acesso dura 15 minutos, traz identificadores de usuário/sessão e exige expiração, issuer, audience e tipo. A chave vem de JWT_SECRET, com pelo menos 32 caracteres e sem default secreto. Sem chave, a autenticação falha com 503; health continua disponível.

Access token deve ficar em memória no frontend e ser enviado em Authorization. Refresh opaco fica no cookie `bpt_refresh`, HttpOnly, SameSite=Strict, Secure e restrito a `/api/v1/auth`. `bpt_csrf` é legível pela interface para compor o header X-CSRF-Token. O nonce CSRF é vinculado ao token por hash no servidor. Origens de browser precisam estar na lista CORS; cookies não usam domínio amplo.

Somente ENVIRONMENT=development pode usar COOKIE_SECURE=false; outra configuração insegura é recusada ao carregar Settings. Produção exige HTTPS e deve manter Secure=true, com frontend e API sob a mesma origem por proxy para compartilhar o cookie CSRF. Não colocar access token em localStorage.

Cada renovação consome o refresh anterior e cria novo par refresh/CSRF. Reutilização de um token consumido com seu nonce válido revoga a família de sessão. As verificações usam locks no banco para evitar duas renovações válidas do mesmo token. A interface deve coordenar uma renovação por vez. Logout invalida também JWTs de acesso já emitidos porque cada requisição verifica o estado da sessão e da conta no banco.

## Senhas e limites

Senha de cadastro: 12 a 128 caracteres, hash Argon2id via pwdlib. Login desconhecido e senha incorreta têm a mesma resposta e executam verificação de hash. E-mail e username são normalizados; username aceita letras minúsculas, números e underscore.

Contadores atômicos PostgreSQL limitam autenticação por minuto: 30 requisições por operação/IP e, quando há identificador, 8 por operação/IP/identificador. Identificador vazio não cria o bucket de oito; refresh/logout/consulta de username preservam o limite de 30 por operação/IP. Credenciais inválidas também consomem limite. Resposta 429 inclui Retry-After=60. O IP vem da conexão; cabeçalhos de proxy arbitrários não são confiados. Configuração de proxy e limpeza de tokens/contadores vencidos integram a operação da Fase 2.

Senhas, JWTs, refresh e nonce CSRF não entram nos logs. O banco armazena apenas hashes dos tokens de refresh e nonce. A dependência `current_user` rejeita sessão ausente, expirada, revogada ou conta inativa; `require_owner` centraliza autoria/admin em propostas e planos; outros módulos aplicam regras próprias, detalhadas no inventário abaixo.

## Papéis e permissões — inventário de 2026-10-23

Inventário de 23/10 conferido na auditoria local de 25/10, com regressões e correções em [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md). F2-02 fica Preparado quanto à operação pública; escopo e pendências no [BACKLOG](../project/BACKLOG.md). Não interpretar esta matriz como certificação de segurança ou ampliação de permissões.

Há somente `USER` e `ADMIN`, persistidos em `users.role`, com constraint no banco. Cadastro cria `USER`; o DTO não aceita `role` nem outros campos extras. A dependência `current_user` verifica token, sessão e conta no banco; as verificações administrativas consultam o papel dessa conta. Visitante não é um terceiro papel persistido. Não existe papel separado de moderador ou revisor.

| Operação | USER | ADMIN / limite atual |
| --- | --- | --- |
| Ler conteúdo público | Sim, assim como visitantes | Sim |
| Criar próprias ideias, propostas, planos e fontes; usar assistência consentida | Sim, sujeito às regras e limites | Sim; ser admin não significa dispensar essas regras |
| Acessar/alterar rascunhos de propostas e planos alheios | Não | Os serviços usam `require_owner`, que aceita autor **ou ADMIN**; preservam regras de estado e imutabilidade. Alcance amplo deve ser revisado na auditoria. |
| Editar/promover ideia privada alheia | Não | O serviço `ideas.owned` exige o autor também para ADMIN. Moderação acessa a fotografia de ideia denunciada, sem abrir toda ideia privada. |
| Manter indicadores/observações, consultar indicadores inativos e solicitar coleta oficial | Não | Sim, rotas administrativas; coleta sujeita aos controles existentes |
| Listar contas e ativar/desativar USER | Não | Sim, com motivo e evento de auditoria. Desativar revoga todas as sessões; reativar exige novo login. A rota recusa alteração de estado de uma conta ADMIN. |
| Escolher ADMIN no cadastro ou trocar role pela rota de gestão de conta | Não | Não nessas rotas. Concessão/revogação de privilégios é assunto operacional a conferir na auditoria; não houve promoção de conta nesta entrega. |
| Ler eventos de auditoria e tratar denúncias de ideias | Não | Sim; pode arquivar a ideia denunciada ou descartar denúncia, com registro |
| Consultar rascunhos de contextos/grafos alheios | Não | Permissão administrativa de leitura prevista nos serviços |
| Editar/publicar contexto ou registro de grafo de outro autor | Não | A escrita/publicação exige o autor; ADMIN não substitui essa autoria. Publicação ainda depende das validações de domínio. |
| Revisar contexto/aresta de outra pessoa para publicação | Não | ADMIN ativo e distinto do autor; não pode aprovar a própria revisão nem tornar aceitação desatualizada em autorização válida |
| Reescrever versão publicada ou composição congelada de plano | Não | Não; imutabilidade também limita ADMIN |
| Consultar/apagar logs de IA de outra conta pelas rotas de histórico | Não | Não; consulta/limpeza filtram o usuário autenticado, sem exceção de ADMIN |

ADMIN, portanto, não é uma autorização universal. Propostas/planos usam uma exceção administrativa ampla; ideias, escrita de contextos/grafos e histórico de IA possuem regras próprias. A auditoria deve verificar essas diferenças e confirmar com o mantenedor se o acesso a rascunhos alheios é o desejado. Mudanças devem respeitar o escopo autorizado e incluir testes de autorização; ampliar acesso a conteúdo privado exige uma decisão específica.

Fontes do inventário: [modelo de usuário](../../backend/app/modules/users/models.py), [cadastro](../../backend/app/modules/auth/schemas.py), [sessão e autoria](../../backend/app/modules/auth/dependencies.py), [administração](../../backend/app/modules/admin/router.py), serviços de [propostas](../../backend/app/modules/policies/service.py), [planos](../../backend/app/modules/plans/service.py), [ideias](../../backend/app/modules/ideas/service.py), [contextos](../../backend/app/modules/contexts/service.py), [grafos](../../backend/app/modules/graphs/service.py) e [histórico privado de IA](../../backend/app/modules/guidance/service.py).

Login serializa a própria conta durante verificação/rehash e criação da sessão. Suspensão administrativa usa a mesma ordem de bloqueio da conta antes de revogar sessões; um login concorrente não deve criar credencial que sobreviva à suspensão e reativação. Esse comportamento foi exercitado em banco temporário isolado.

Senhas têm hash Argon2id, não criptografia reversível; JWT é assinado, não cifrado. Dados pessoais/textos e volumes não são criptografados por campo pela aplicação. Engine oculta parâmetros SQL; erros de banco e configuração não devem ecoar dados privados. Limites e distinção entre transporte local e HTTPS em [SECURITY_AUDIT](../governance/SECURITY_AUDIT.md).

## Configurar

Na raiz, `powershell -File scripts/setup-local.ps1` cria ambientes ausentes e uma chave aleatória, preservando arquivos existentes. Ajuste DATABASE_URL para seu banco e execute `uv run alembic upgrade head` em backend. Em produção, forneça JWT_SECRET pelo gerenciador de secrets e mantenha cookies seguros.

## Referências

- [FastAPI: JWT e hash de senhas](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [PyJWT: verificação de claims](https://pyjwt.readthedocs.io/en/stable/usage.html)
- [OWASP: prevenção de CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
