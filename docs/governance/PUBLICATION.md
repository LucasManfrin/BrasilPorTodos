# Publicar o código e lançar o serviço

Estado atualizado em 2026-10-23. Repositório organizado, licença MIT, exemplos de ambiente sem segredo real, CI/templates e guias de agentes disponíveis. Registro local em Git autorizado pelo mantenedor e revisado nesta entrega. Não há remoto, push ou publicação externa. [Auditoria](../project/REPOSITORY_AUDIT.md).

## Abrir o repositório no GitHub

1. Revisar `git status --short` e `git diff --cached` após selecionar os arquivos do primeiro commit. `.env`, `.local`, bancos, caches e logs devem continuar excluídos. Não publicar dados de contas ou dumps da demonstração.
2. Rodar os checks do [guia de desenvolvimento](../development/DEVELOPMENT.md). O relatório local não substitui executar a CI no GitHub.
3. Criar o repositório/remoto escolhido pelo mantenedor e enviar os commits locais. Configuração do remoto, push e publicação externa dependem de instrução própria; não foram executados nesta auditoria.
4. Conferir a CI no remoto. Só após a primeira execução configurar a proteção de main e checks obrigatórios usando os nomes reais dos jobs; nenhuma aprovação/revisão é dispensada por este documento.
5. Definir canal público de contato e habilitar/configurar reporte privado de vulnerabilidades, atualizando [SECURITY.md](../../SECURITY.md). Não publicar vulnerabilidades com dados privados em issues abertas.
6. Configurar NEXT_PUBLIC_REPOSITORY_URL e contato quando existirem; gerar novo build. Remover afirmações de ausência de remoto dos documentos somente depois da configuração real.

`package.json` com private=true evita publicação acidental no registro npm; não impede o código de ser open source no GitHub. A licença MIT cobre código e documentação autoral; [termos de dados/fontes/conteúdo](LICENSING.md) são separados.

A revisão local conferiu exclusões de arquivos e padrões comuns de credenciais nos candidatos ao primeiro commit, sem apontar ocorrências. É uma revisão limitada, não garantia de ausência de todos os segredos ou vulnerabilidades de dependências. Não foi feito upload para ferramenta externa.

## Lançar a plataforma com cadastro público

Abrir o código não torna o serviço pronto para operação pública. Ainda precisam ser concluídos:

- Política de conteúdo e privacidade vigentes, aceite versionado, atribuição e procedimentos de retirada. [docs/governance/CONTENT_POLICY_DRAFT.md](CONTENT_POLICY_DRAFT.md) continua proposta, sem vigência.
- Hospedagem/origem, HTTPS, secrets, cookies seguros, proxy/IP confiável, limites e limpeza/retenção de sessões.
- Backup/restauração local já exercitados; ainda definir política de backups da hospedagem, testar restauração nesse ambiente, migrations de implantação, monitoramento de API/coleta e responsável operacional.
- Worker persistente/supervisionado, status de falhas, revisão da cobertura de dados e condições de uso/exportação.
- Fluxo completo em ambiente de lançamento, acessibilidade aprofundada, canais de manutenção e teste de carga compatível.
- UI-06 já dispõe localmente de limites diários, denúncias/moderação, compartilhamento explícito e ordenação documental; o roteiro público/versionado, consentimento e controles de logs/quotas também estão implementados. Gemini real já foi configurado e conferido localmente; ainda registrar avaliação sistemática de imparcialidade (UI-06C/F). Nos exemplos distribuídos permanece desativado por padrão. A capacidade local não dispensa termos/privacidade, moderação responsável, carga/proxy e operação de lançamento. Revisão técnica de propostas segue `NOT_ASSESSED`, sem selo inventado. [Requisito](../product/PROPOSAL_CREATION.md).

## Docker e ambiente atual

Compose completo local validado em 2026-10-20: PostgreSQL, migrations, API, frontend e limpeza de logs. Configura autenticação, origens/cookies HTTP locais e prontidão; banco em volume próprio e interfaces em loopback. [Guia](../development/DOCKER_LOCAL.md). Não habilita automaticamente coleta oficial/Gemini nem atende HTTPS, termos e supervisão de lançamento público.

## Pendências rastreadas

F0-06/F0-04: remoto, proteção e CI real; F1-11/UI-05: canais; F1-14: conteúdo/privacidade; F2-01/02/03/04: acessibilidade, segurança/limites, operação e qualidade de dados. Consulte os estados atuais no [backlog](../project/BACKLOG.md); o documento não muda esses itens para concluídos.


## Atribuição e comunicação da EFGG — DATA-07B3

A integração usa os [termos do Tesouro Transparente](https://www.tesourotransparente.gov.br/sobre/dados-abertos/termos-de-uso), com nome STN/URL e sem logomarca ou alegação de endosso. Item 6 pede informar a STN pelo Fale Conosco sobre produtos que utilizam seus dados. Pendência real: preparar e registrar comunicação pelo mantenedor, com descrição do BrasilPorTodos, dados EFGG/ano/consolidação e endereço público quando houver. Nenhum envio foi autorizado ou executado; não inventar remetente, contato ou URL pública. [Contrato dos dados](../data/GENERAL_GOVERNMENT.md).


## Entrega local e assistência opcional — estado em 2026-10-23

O mantenedor optou por usar o projeto no próprio computador. Launchers e backup/restauração local estão disponíveis; não foi aberto serviço público, criado remoto, feito push/deploy ou aceito termo em nome do mantenedor. O histórico Git é local. Roteiro de apresentação acadêmica não faz parte desta entrega.

Gemini foi escolhido para assistência opcional: desenvolve a redação e oferece possibilidades separadas para o autor avaliar, sem calcular impactos ou preencher campos automaticamente. Prompt 4.0.0; validação de formato/tamanho, sem rejeição por comparação semântica. Integração desligada por padrão nos exemplos, chave só no backend e consentimento antes do envio. Configuração e chamada real já conferidas localmente; avaliação sistemática do modelo permanece pendente. Logs privados têm expiração padrão sete dias e apagamento do conteúdo pelo usuário, mantendo quota mínima. Limpeza depende de processo ativo, não elimina backups automaticamente nem garante execução com computador desligado. Lançamento exige informar também tratamento pelo provedor e política efetiva de retenção/backups. [Contrato](../product/PROPOSAL_CREATION.md) · [Operação](../development/DEVELOPMENT.md).

Conteúdo real de desemprego continua privado aguardando revisão humana e termos da pesquisa; primeiro mapa real de FGTS ainda exige pesquisa/curadoria. Exemplos e QA não servem como aprovação de pessoas. A entrega local não encerra esses gates nem GRAPH-01D/E, qualidade representativa de hardware/leitor de tela ou toda a Fase 2.
