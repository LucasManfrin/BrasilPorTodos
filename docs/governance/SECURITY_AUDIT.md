# Auditoria de autenticação e autorização — 2026-10-25

## Parecer e alcance

A autenticação possui uma base coerente: hash de senha adequado, tokens curtos, refresh rotativo, revogação persistida, CSRF e autorização no servidor. A revisão não identificou um bypass de role ou acesso horizontal além das permissões administrativas explícitas. Isso não é certificação de segurança nem garantia de ausência de falhas.

Foram revisados código, dependências, configuração local e testes de autenticação/roles. Houve correções e regressões em banco PostgreSQL temporário exclusivo, com dados fictícios. Não houve pentest em terceiros, leitura de payloads privados da IA, mudança de senha/chaves, promoção/desativação de contas reais, coleta oficial ou publicação externa. Banco/volume útil preservados; schema e motor fiscal não foram alterados.

**Uso local:** adequado ao estágio de desenvolvimento, com os limites abaixo. **Serviço público:** continua pendente, principalmente por HTTPS, privilégios do banco, proxy/rate limit e operação das contas administrativas. F2-02 fica Preparado: auditoria local entregue, requisitos de operação pública abertos.

## Achados e correções

| Achado | Severidade / alcance | Resultado |
| --- | --- | --- |
| Next.js 16.4.0 com três avisos conhecidos, incluindo dois de execução remota e um de negação de serviço | Crítica na dependência; não foi executado exploit nem demonstrada exploração nesta configuração | Next.js e eslint-config-next atualizados para 16.4.3; sharp 0.35.5/librsvg 2.63.2 conferidos. Auditoria npm de produção e completa zeradas; build nativo e Docker passaram. |
| Zod 4.6.5 transitivo das ferramentas de desenvolvimento | Alta no catálogo de dependências; não era dependência de execução da aplicação | Patch transitivo compatível para 4.6.7 no lockfile, sem adicionar dependência direta/override. Lint e auditoria completa passaram. |
| Desativar USER apenas mudava is_active; reativar permitia reutilizar sessões antigas ainda válidas | Média; a conta inativa já recusava acesso | Desativação revoga todas as sessões na mesma transação. Reativar exige novo login. Login usa bloqueio exclusivo na própria conta, também seguro para atualização do hash, para ordenar criação de sessão e suspensão concorrentes. |
| Configuração aceitava COOKIE_SECURE=false fora de development | Média, erro de configuração antes de exposição pública | Settings agora recusa essa combinação fora de ENVIRONMENT=development. HTTP local explícito continua permitido; não foi instalado HTTPS artificial no localhost. |
| Bucket de identidade vazio aplicava 8/min a refresh/logout/consulta de username | Média de disponibilidade; impacto maior com proxy compartilhado | Limite por identidade só existe quando há identificador. Limite por operação/IP de 30/min mantido. O problema de IP compartilhado no proxy continua uma pendência distinta. |
| Exceções SQL poderiam levar parâmetros privados ao traceback | Média potencial de confidencialidade; não foi observado vazamento real | Engine com hide_parameters=True; tratamento de SQLAlchemyError retorna erro genérico e registra somente classe e request_id. Mensagem bruta do driver não é registrada pelo handler, pois também pode embutir valores. |
| Erros de validação de configuração podiam imprimir a entrada bruta, incluindo segredos | Média potencial de confidencialidade em startup mal configurado | Core, assistência e limites de participação usam hide_input_in_errors=True; testes com valores fictícios verificam ausência da entrada em str(ValidationError). Não imprimir .errors() ou dumps de settings sem sanitizar. |
| Claim sid com tipo inesperado em um token assinado podia gerar erro interno | Baixa, robustez de contrato; não permite forjar assinatura | Identificadores exigidos como texto e UUID válido; regressões verificam recusa 401, sem erro 500. |

Fontes do framework: avisos dos mantenedores sobre [imagem/SVG](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw), [use cache](https://github.com/vercel/next.js/security/advisories/GHSA-673q-mjm6-r5xr) e [Server Actions](https://github.com/vercel/next.js/security/advisories/GHSA-p3m5-59mp-jv5r); [release 16.4.3](https://github.com/vercel/next.js/releases/tag/v16.4.3). Não foi inferido que o projeto era explorável em todos esses caminhos. O patch não depende dessa suposição.

## Senhas, criptografia e o que fica legível

| Dado / trecho | Proteção atual | Limite |
| --- | --- | --- |
| Senha de usuário | Argon2id com salt por hash, via pwdlib; parâmetros conferidos: 65.536 KiB de memória, 3 iterações, paralelismo 4 | É hash de mão única, não criptografia reversível. A aplicação não consegue recuperar a senha original. Cadastro aceita 12–128 caracteres; não há verificação de senha vazada ou MFA. |
| JWT de acesso | Assinatura HMAC-SHA256 (HS256), chave no backend, validade padrão 15 minutos | Assinatura impede alteração sem a chave; **não esconde o conteúdo**. Payload é decodificável. Não colocar segredos nele. |
| Refresh e nonce CSRF no banco | Segredos aleatórios de alta entropia; SHA-256 dos valores armazenados, comparação CSRF com hmac.compare_digest | Hash rápido é adequado para esses tokens aleatórios; não substituir Argon2id de senhas por SHA-256. Valores de refresh ficam no navegador em cookie, não são devolvidos como hash para autenticar. |
| Navegador → site/API local | HTTP restrito a loopback no Compose; cookies Secure=false somente em development | **Não há criptografia TLS nesse trecho local.** Produção exige HTTPS e cookies Secure. Loopback não elimina riscos de uma máquina comprometida. |
| Backend → Gemini | HTTPS com verificação TLS padrão, host fixo e sem seguir redirecionamento; chave em header | O provedor recebe o conteúdo consentido. HTTPS não elimina a necessidade de política de privacidade/retenção. Nenhuma chamada real ao modelo foi feita nesta auditoria. |
| API → PostgreSQL local | Rede interna Docker; porta publicada só em 127.0.0.1 | PostgreSQL conferido com ssl=off. Não há TLS configurado nesse trecho; definir transporte apropriado se banco sair do host/rede local controlada. |
| Nome/e-mail, rascunhos e registros privados de IA | Autorização e isolamento lógico por conta | Não possuem criptografia por campo na aplicação. Quem tiver acesso privilegiado ao banco pode lê-los. |
| Volume PostgreSQL, backups e arquivos .env | Arquivos locais/volume e exclusões do Git | Compose não estabelece criptografia em repouso; não foi verificado BitLocker ou proteção do disco do host. .env não é um cofre criptográfico. Definir criptografia e acesso a disco/backups no ambiente final. |

JWT_SECRET exige no mínimo 32 caracteres, não tem segredo padrão e agora rejeita valor só com espaços. Chave ausente mantém autenticação indisponível (503), sem abrir acesso. Isso não mede a entropia de uma chave escolhida manualmente. Configuração local tem chave definida, sem imprimir seu valor. Chaves previamente compartilhadas fora do ambiente devem ser substituídas se ainda estiverem vigentes; não houve rotação nesta entrega.

As escolhas de hash/sessão foram comparadas às referências [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) e [Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html). Consulta de referência não equivale a certificação OWASP.

## Login, sessão e proteção do navegador

- Cadastro cria USER, normaliza e-mail/username, valida tamanhos e rejeita campos extras como role. Senhas incorretas e contas inexistentes recebem a mesma resposta de login; a verificação de hash também ocorre para conta inexistente.
- JWT exige sub, sid, jti, type, iat, nbf, exp, issuer e audience; o decode aceita somente HS256. Tipos, assinatura, audiência/emissor, expiração e sessão correspondente são verificados.
- Cada requisição autenticada verifica a sessão e a conta no banco: conta inativa, sessão expirada/revogada ou sessão de outro usuário não passa. Um JWT válido não dispensa essa consulta.
- Access token fica em memória do frontend, sem persistência em localStorage. Refresh fica em cookie HttpOnly, SameSite=Strict e caminho /api/v1/auth. O cookie CSRF é legível pelo JavaScript por finalidade: seu valor vai no header e deve corresponder ao hash vinculado ao refresh no servidor.
- Refresh consome o token anterior e emite outro par. Reuso autenticado do token consumido revoga a família de sessão; locks serializam a rotação. Logout invalida também os JWTs já emitidos daquela sessão.
- Origem de browser não permitida é rejeitada nos fluxos de conta. Respostas privadas/autenticadas não devem ser cacheadas. Escrita de conteúdo exige bearer token; cookies sozinhos não autorizam alterações de rascunhos.
- Logs HTTP próprios omitem body, Authorization, cookies e query string. O access log padrão do servidor pode registrar URL/query; o relatório não promete ausência de todo dado em qualquer log. Handler SQL foi endurecido, mas revisão operacional de logs continua necessária.

## Roles e autorização

Existem somente USER e ADMIN. O papel está em users.role, com constraint no banco. O backend consulta a conta atual; não aceita um role informado pelo formulário, frontend ou claim adicional do JWT como fonte de autorização. Ocultar botões na interface não é o controle de segurança. A checagem por requisição segue o princípio descrito em [OWASP Authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).

| Ação | USER | ADMIN |
| --- | --- | --- |
| Ler publicações | Sim; visitantes também | Sim |
| Criar/editar contribuições próprias | Sim, com validações e limites | Sim, com validações e limites |
| Acessar/alterar/publicar rascunhos de propostas e planos alheios | Não | Permissão explícita em require_owner; não foi removida silenciosamente |
| Manter indicadores/observações e solicitar coleta | Não | Sim |
| Listar contas, ativar/desativar USER e consultar auditoria | Não | Sim, com motivo/auditoria; desativação revoga sessões |
| Tratar denúncias e arquivar ideia denunciada | Não | Sim, a partir da fotografia da denúncia |
| Abrir/editar/promover qualquer ideia privada alheia | Não | Não; exige autor |
| Ler rascunhos de contextos/grafos para revisão | Só próprios | Sim |
| Editar/publicar contexto ou registro de grafo alheio | Não | Não; publicação continua autoral e sujeita à revisão |
| Revisar contexto/aresta | Não | Sim, se não for o autor e estiver ativo |
| Reescrever conteúdo já publicado ou plano congelado | Não | Não |
| Ler/apagar histórico de IA alheio pelas rotas atuais | Não | Não; filtro pelo proprietário |

Acesso direto ao PostgreSQL é outro nível de privilégio: um administrador do banco não está limitado pelas roles da aplicação. **A conta SQL local foi conferida como superuser e com permissão de criar bancos**, padrão do bootstrap PostgreSQL usado no desenvolvimento. Isso facilita migrations/testes locais, mas é privilégio excessivo para a aplicação em produção. Separar usuário de execução com privilégios mínimos de usuário de migrations/manutenção antes do lançamento; não foram alterados privilégios do banco útil nesta entrega.

ADMIN amplo em propostas/planos é uma decisão existente de produto. Deve ser confirmado antes de abrir conteúdo privado de participantes públicos. Não foi identificado bypass disso por USER nos testes/revisão, nem se concedeu ADMIN a contas reais. O CLI bootstrap-admin usa lock de tabela, motivo e auditoria para o primeiro administrador; não é um fluxo completo de concessão/revogação/recuperação de administradores.

## Pendências antes de serviço público

1. **Alta:** retirar superuser da conta de execução do banco; definir HTTPS, cookies Secure, origem/proxy e transporte do banco no ambiente final. Separar credenciais de aplicação, migração e manutenção.
2. **Média:** proxy Next faz usuários compartilharem o IP visto pela API. Os limites de 30/min por operação/IP e 8/min por IP+identificador continuam podendo causar bloqueio compartilhado. Não há limitação distribuída independente por conta. Definir proxy confiável e testar carga; não confiar livremente em X-Forwarded-For/X-Real-IP.
3. **Média:** operação de contas ainda não tem MFA, recuperação/troca de senha, verificação de e-mail ou procedimento completo de revogação/recuperação de ADMIN. Priorizar proteção da conta administrativa e decidir requisitos de cadastro público.
4. **Média:** falta limpeza operacional de sessões, refresh e contadores expirados. Sessões expiradas são recusadas, mas registros podem crescer. Worker de limpeza da IA não limpa essas tabelas.
5. **Disponibilidade:** refresh coordenado dentro da aba; abas concorrentes podem disparar detecção de reuso e encerrar a sessão. Não relaxar a proteção de replay sem projetar coordenação adequada entre abas.
6. **Defesa adicional:** retenção/acesso de logs e backups, segurança do host, limites de tamanho/carga e headers de segurança no ambiente final. Não foram auditados disco, sistema operacional, rede pública ou supply chain completa.

Termos/privacidade vigentes e avaliação sistemática do modelo são gates separados. Dados oficiais/coleta e análise final com IA/grafos não foram implementados por esta auditoria de autenticação.

## Evidências e limites dos testes

- **1.447 testes backend passaram** em PostgreSQL temporário exclusivo, incluindo 37 novas regressões. Abrangem claims/assinatura/expiração, sessão de outra conta, claim de role ignorada, demissão de ADMIN, suspensão/reativação, cookies, origem, limites, IDs e sigilo dos erros SQL/configuração. Ruff/check de formatação passaram em 190 arquivos.
- Houve rodada focal de **48 testes** após ajustar o bloqueio do login, antes dos três casos adicionais de sigilo de configuração incluídos na suíte final. Experimento separado em banco descartável confirmou login concorrente à suspensão, bloqueio observado e acesso/refresh antigos 401 após reativação. O observador do experimento foi ajustado para atualizar estatísticas a cada consulta; a rodada final passou. Esse experimento não é benchmark de carga.
- **320 testes frontend**, ESLint, TypeScript e build nativo passaram. Build Docker do frontend/API passou. Next.js **16.4.3 confirmado no container em execução**; as flags de sigilo de configuração também foram conferidas no runtime.
- `npm audit --omit=dev` e auditoria npm completa: **zero alertas conhecidos** após os patches. `pip-audit`: **45 distribuições** no ambiente Python local e **35 na imagem Linux**, zero alertas conhecidos e zero pacotes ignorados nos dois conjuntos.
- Compose local ativo, migrations no head sem mudança de schema, PostgreSQL preservado. Health/ready e tela de entrada responderam 200; administração anônima 401. Pelo proxy real, login fictício inválido retornou 401, origem não permitida 403 e resposta no-store. Não foram criadas contas reais para essa checagem.
- Documentos/links e diff de whitespace passaram. Nenhum segredo/ambiente ou payload privado deve ser incluído no Git; revisão dos candidatos antes dos commits, sem envio a ferramenta externa de código.
- Não foram repetidos QA visual responsivo/leitor de tela nesta fatia sem alteração de telas, nem feitos pentest externo, scan de pacotes do sistema operacional, verificação do disco/BitLocker ou teste de carga distribuída.


Os resultados locais não substituem CI remota ou pentest independente. Zero avisos em scanners significa zero avisos conhecidos nas bases consultadas, não ausência de vulnerabilidades desconhecidas. Dependências do sistema operacional da imagem não foram escaneadas. As referências históricas de 23/10 permanecem em [REPOSITORY_AUDIT](../project/REPOSITORY_AUDIT.md); os achados do framework foram corrigidos nesta entrega, não retroativamente naquela auditoria.
