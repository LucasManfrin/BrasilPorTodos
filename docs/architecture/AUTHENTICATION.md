# Contas e sessões

Backend e interface implementados em F1-02/F1-10. O token de acesso fica em memória; renovação coordena uma requisição por vez. O proxy Next.js preserva os dois cookies e cabeçalhos de sessão sob a mesma origem.

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

Desenvolvimento local pode usar COOKIE_SECURE=false. Produção exige HTTPS e deve manter Secure=true, com frontend e API sob a mesma origem por proxy para compartilhar o cookie CSRF. Não colocar access token em localStorage.

Cada renovação consome o refresh anterior e cria novo par refresh/CSRF. Reutilização de um token consumido com seu nonce válido revoga a família de sessão. As verificações usam locks no banco para evitar duas renovações válidas do mesmo token. A interface deve coordenar uma renovação por vez. Logout invalida também JWTs de acesso já emitidos porque cada requisição verifica o estado da sessão e da conta no banco.

## Senhas e limites

Senha de cadastro: 12 a 128 caracteres, hash Argon2id via pwdlib. Login desconhecido e senha incorreta têm a mesma resposta e executam verificação de hash. E-mail e username são normalizados; username aceita letras minúsculas, números e underscore.

Contadores atômicos PostgreSQL limitam autenticação por minuto: 30 requisições por operação/IP e 8 por operação/IP/identificador. Credenciais inválidas também consomem limite. Resposta 429 inclui Retry-After=60. O IP vem da conexão; cabeçalhos de proxy arbitrários não são confiados. Configuração de proxy e limpeza de tokens/contadores vencidos integram a operação da Fase 2.

Senhas, JWTs, refresh e nonce CSRF não entram nos logs. O banco armazena apenas hashes dos tokens de refresh e nonce. A dependência `current_user` rejeita sessão ausente, expirada, revogada ou conta inativa; `require_owner` centraliza autoria/admin para os próximos módulos.

## Configurar

Na raiz, `powershell -File scripts/setup-local.ps1` cria ambientes ausentes e uma chave aleatória, preservando arquivos existentes. Ajuste DATABASE_URL para seu banco e execute `uv run alembic upgrade head` em backend. Em produção, forneça JWT_SECRET pelo gerenciador de secrets e mantenha cookies seguros.

## Referências

- [FastAPI: JWT e hash de senhas](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [PyJWT: verificação de claims](https://pyjwt.readthedocs.io/en/stable/usage.html)
- [OWASP: prevenção de CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
