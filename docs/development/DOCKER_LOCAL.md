# Docker local

O Compose executa PostgreSQL 17, migrations Alembic, FastAPI, Next.js, coletor diário de fontes oficiais e limpeza de logs expirados de assistência. Imagens da aplicação são construídas localmente com os lockfiles; não são publicadas. Não é necessário instalar Node/Python no host para usar esse fluxo.

## Iniciar

Com Docker Desktop em modo de containers Linux, execute na raiz:

```powershell
powershell -NoProfile -File scripts/setup-docker.ps1
docker compose up -d --build --wait
docker compose ps -a
```

O setup preserva arquivos existentes e cria os ausentes com segredos aleatórios. Se a execução nativa estiver usando 3000/8000, encerre somente os serviços gerenciados com `powershell -NoProfile -File scripts/stop-local.ps1` antes do Compose. O PostgreSQL nativo é preservado.

Em Linux/macOS, copie `.env.example` para `.env` na raiz e `backend/.env.example` para `backend/.env`; gere `POSTGRES_PASSWORD` hexadecimal aleatória e `JWT_SECRET` aleatório de pelo menos 32 caracteres. Os valores vazios dos exemplos não são credenciais utilizáveis. Depois execute o mesmo comando Compose.

Abra http://127.0.0.1:3000 ou http://localhost:3000. API: http://127.0.0.1:8000/docs. Prontidão do conjunto: http://127.0.0.1:3000/api/v1/ready. O serviço `migrate` termina com código 0; isso é esperado. API/frontend têm checagens TCP das portas locais: a pedido do mantenedor, não fazem mais chamadas HTTP periódicas a /ready. Isso verifica conexão, não valida banco ou conteúdo da API; /ready continua disponível para diagnóstico manual. A limpeza é processo contínuo sem healthcheck próprio: consulte seus logs, não interprete somente processo vivo como exclusão confirmada.

## Configuração

| Arquivo | Conteúdo |
| --- | --- |
| `.env` da raiz | Senha do PostgreSQL Docker e portas do host: banco 5433, API 8000, site 3000 por padrão |
| `backend/.env` | JWT_SECRET, configuração Gemini e limites do backend; nunca enviar ao Git ou ao frontend |
| `frontend/.env.local` | Somente execução nativa; não entra na imagem Docker |

Dentro do Compose, `DATABASE_URL` é sobrescrita para o host de rede `postgres:5432`; `localhost` dentro do container não aponta ao banco. O Next usa `API_INTERNAL_URL=http://backend:8000` em tempo de execução. CORS acompanha a porta do frontend, cookies locais HTTP usam `COOKIE_SECURE=false`, e `ENVIRONMENT=development` mantém a demonstração local. Isso não é configuração para exposição pública. Todas as portas publicadas ficam em loopback.

O frontend roda como `node` e a API como `appuser`. Segredos, dumps, dados `.local`, caches e dependências nativas são excluídos do contexto/imagens; nenhuma chave Gemini é argumento de build.

A chave Gemini, quando disponível, vai em `GEMINI_API_KEY` de `backend/.env`; habilite somente após configurar e avaliar conforme [desenvolvimento](DEVELOPMENT.md#assistência-opcional-gemini). Recrie backend, guidance-cleanup e indicator-collector para reler variáveis compartilhadas. Sem chave, o modo guiado literal funciona. Não houve chamada real de IA na validação Docker.

## Dados e atualização do código

O banco usa o volume `postgres_data` do projeto Compose. Uma instalação nova começa vazia; o comando de início não importa o banco nativo, cria conta padrão nem semeia dados. O coletor consulta fontes oficiais quando já existe ADMIN ativo e a agenda está vencida; sem administrador, aguarda sem criar/promover conta. Para trazer uma instalação existente, faça backup e restaure somente em destino vazio, conferindo compatibilidade das versões PostgreSQL e os registros. Não restaure por cima de um banco já usado. A cópia local desta migração foi conferida em [VERIFICATION](VERIFICATION.md); a origem permanece separada e não sincroniza alterações feitas depois.

Após mudar o código, faça backup do volume usado e execute novamente `docker compose up -d --build --wait`. O serviço `migrate` aplica apenas upgrades antes da API. Não remover volumes para aplicar migrations. Caso use serviços de outro diretório, execute sempre os comandos na raiz correta.

```powershell
# Parar sem remover containers nem dados
docker compose stop
# Retomar, executar migrations pendentes e conferir saúde
docker compose up -d --wait
# Logs sem imprimir configuração/segredos
docker compose logs --tail 50 backend frontend guidance-cleanup indicator-collector
```

`docker compose down` remove os containers/rede e conserva o volume. A opção `-v` apaga o banco: não usar para reiniciar ou atualizar. Trocar `POSTGRES_PASSWORD` no arquivo não altera a senha de um volume já inicializado; preserve sua configuração ou faça rotação explícita no banco.

O serviço `indicator-collector` exige ADMIN ativo e roda diariamente às **00:00 de São Paulo**, com retomada de consulta vencida ao iniciar e nova tentativa após uma hora em caso de falha parcial. Mantém o lock global no PostgreSQL e preserva dados anteriores de fontes indisponíveis. Não faz consulta por visitante nem sondagens HTTP de /ready. O PC/Docker precisam estar ligados; o agendamento configurado na página não prova que o worker está vivo. Confira seus logs e o resultado por fonte. Veja configuração, atribuição e execução nativa em [indicadores](../data/INDICATORS.md). A limpeza de IA executa a cada 300 segundos enquanto o container estiver ativo; backups têm retenção própria.

Se uma porta estiver ocupada ou bloqueada pelo Windows, altere somente a porta correspondente no `.env` da raiz e recrie com `docker compose up -d --wait`. Não encerre serviços de outros projetos. A porta interna do banco continua 5432.

## Backup

Use uma pasta privada ignorada pelo Git, como `.local/backups`. Para evitar corrupção de arquivo binário por redirecionamento no Windows PowerShell, gere o dump no container e copie o arquivo:

```powershell
New-Item -ItemType Directory -Force .local/backups
docker compose exec -T postgres pg_dump -U brasil -d brasil_portodos -Fc -f /tmp/brasil-backup.dump
docker compose cp postgres:/tmp/brasil-backup.dump .local/backups/brasil-backup.dump
```

Escolha nomes novos para preservar backups anteriores. Dumps contêm dados privados; nunca publicá-los. Política de backup automático, restauração no ambiente de hospedagem, HTTPS e monitoramento público seguem em [publicação](../governance/PUBLICATION.md).

Referências: [ordem e prontidão no Compose](https://docs.docker.com/compose/how-tos/startup-order/), [precedência das variáveis](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/).
