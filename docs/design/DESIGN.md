# Interface do BrasilPorTodos

Direção solicitada pelo mantenedor em 2026-10-06: produto moderno, brasileiro, com linguagem direta, pensado primeiro para celular e sem associação a partido ou candidatura.

## Sistema visual

- Todas as cores, superfícies dos temas, raios e largura máxima estão em `frontend/src/app/tokens.css`.
- Verde `#009C3B`, amarelo `#FFDF00`, azul `#002776`, branco e texto quase-preto. Branco não é usado como texto de corpo sobre o verde: esse par não atende AA para texto pequeno.
- Bricolage Grotesque nos títulos e DM Sans no corpo, por `next/font`, com `display: swap`, fallback ajustado e fontes servidas pelo próprio Next. Corpo, avisos e controles têm pelo menos 16 px.
- Seções de ponta a ponta, container de até 1440 px, grids de 12 colunas no desktop e composição em coluna no celular. Nenhum conteúdo funcional depende das formas decorativas.
- Claro/escuro seguem a preferência do sistema. O botão de tema salva somente `bpt-theme`, uma preferência visual; credenciais continuam fora do armazenamento local.
- Geometria abstrata em CSS e SVGs próprios; nenhum pacote de ícones, animação ou imagens de terceiros foi adicionado. Sem bandeira literal, símbolos partidários, neon ou efeito de vidro.

## Componentes

`Button`, `Card`, `Section`, `Icon`, `Navbar`, `ThemeToggle`, `ContributionCard` e `ImpactMeter` usam os mesmos tokens. Estilos de formulários, tabelas, avisos e painel preservam os contratos e interações existentes. Loading, erro inesperado e 404 têm telas próprias.

Navbar fixa ao rolar, CTA de criar proposta e menu mobile com disclosure nativo. Escape fecha o menu e devolve foco ao controle; mudar de rota também fecha o menu. O link de pular conteúdo aponta a um main focável. Campos usam labels, resultados do exemplo são anunciados por `aria-live` e barras têm uma descrição textual dos valores.

Microinterações incluem resposta de botões/cards, animação da barra ao alterar controles e contagem ao entrar na tela. `prefers-reduced-motion` desativa transições/animações e a contagem animada. A home mantém dimensões da composição e números tabulares; não depende de imagens carregadas depois.

## Conteúdo e honestidade dos números

A home explica a motivação: em eleições, acompanhar dados e propostas ao mesmo tempo é difícil; a plataforma organiza as escolhas para permitir entender custos, financiamento e limites sem precisar dominar tudo.

O hero usa valores **fictícios** em bilhões: despesa ajustável, receita ajustável e economia fixa de 10. O saldo é receita + economia − despesa. Não é uma consulta a dados oficiais nem uma previsão do orçamento. Exemplos de Saúde e Educação também são fictícios e não são recomendações.

Nos cards publicados, o medidor soma impactos em centavos com BigInt, sem converter dinheiro a ponto flutuante. Mostra somente o saldo incremental das medidas estimadas, e nunca afirma que o orçamento brasileiro “fecha”. Sem estimativa é diferente de zero. Valores de financiamento declarativo não são contados como receita novamente. Planos usam sua simulação publicada; avisos de financiamento continuam visíveis.

## Duplicação

Duplicar exige sessão e chama a criação existente de proposta/plano. Cria identidade nova e rascunho privado, sem publicar ou alterar o original. A cópia registra autor, número de versão e caminho da publicação original em `change_summary`. Propostas copiam impactos, declarações de financiamento e referências. Planos preservam os IDs das versões incluídas; uma execução nova exige simular novamente.

É uma cópia independente, não um grafo de forks ou sincronização de contribuições. Revisar fontes, termos e premissas antes de republicar. A política de conteúdo da plataforma permanece pendente em ADR-019.

Apoiar e comentar aparecem desabilitados com explicação. Não há votos, contadores ou comentários falsos. Habilitá-los exige implementação e regras de moderação; ver UI-04 no backlog.

## Rodapé e configuração

Metodologia, transparência e fontes são acessíveis sem login. `NEXT_PUBLIC_REPOSITORY_URL` e `NEXT_PUBLIC_CONTACT_EMAIL` configuram os canais públicos. Sem esses dados, o rodapé indica preparação; o link de código aberto leva à transparência, que explica a ausência de remoto público.

## Verificação

O roteiro e evidências do redesign ficam em [docs/development/E2E.md](../development/E2E.md). Medir largura do documento, verificar conteúdo, foco/teclado e os dois temas nos tamanhos 360, 768, 1280 e 1920. Tabelas largas têm rolagem interna, sem alargar a página. A revisão de contraste cobre os pares renderizados de texto; não substitui uma auditoria completa com leitores de tela.

Avisos e licenças integrais das fontes estão preservados em frontend/public/licenses e vinculados em docs/governance/LICENSING.md.

Para reduzir o payload da lista no celular, as ações do card recebem apenas slug e número de versão. O conteúdo completo é consultado pela rota pública de versão somente ao clicar em Duplicar, preservando a versão que estava exibida mesmo se outra publicação surgir depois.

## Páginas internas — 2026-10-07

Home preservada. Brasil Atual tem banda azul, sparklines com escala declarada, comparações em p.p./%, método recolhido, filtros em chips e botão para usar o indicador em uma proposta. Detalhe oferece seleção de período sem inventar pontos ausentes. Propostas usam banda amarela e planos verde; fontes mostram instituição, termos, referências publicadas e filtros.

Cadastro/entrada usam formulário com largura confortável e composição geométrica lateral, escondida no celular; navegação reduzida, autocomplete, mostrar senha e disponibilidade de username. Aviso de termos em preparação não é aceite de termos vigentes; login Google permanece pendente.

Editor de proposta usa cinco etapas, autosave privado e prévia fiscal; editor de plano mantém balanço fixo na lateral e recomputa ao selecionar medidas/anos. Valores incompletos geram parcial, não zero garantido. Atualização de base do rascunho é explícita. Apoios/comentários e ordenação social aguardam persistência e moderação; não há números de engajamento fictícios. Compartilhamento usa link público, e exemplos locais têm marca própria.

## Exploração de dados — 2026-10-10

Brasil Atual e Fontes usam componentes locais para destaques, drawer, gráficos SVG e tabela por instituição. Critérios fixos, formatação, comparações e deduplicação em [docs/design/DATA_EXPLORER.md](DATA_EXPLORER.md). Tokens e componentes compartilhados permanecem preservados.

## Rede em profundidade — 2026-10-15

GRAPH-01C usa palco azul profundo, pontos facetados com quatro formas, linhas direcionais e perspectiva 3D real por projeção de coordenadas. Composição ampla mantém tokens existentes, dois temas e inspeção legível na lateral; no celular o detalhe fica abaixo com foco/retorno e lista equivalente. Sem glow, vidro, cores partidárias ou biblioteca visual nova. Origem/destino e sentido ficam em texto; amarelo indica seleção, sem usar verde/vermelho como juízo sobre o resultado.

Rotação/movimento/zoom são visuais; tamanho/proximidade não codificam força, certeza ou valor. Relações incertas são tracejadas e identificadas em texto ao abrir. A legenda explica pontos/linhas e o guia ensina a leitura. O exemplo tem faixa amarela fixa de identificação; erro não vira dado fictício. [Requisito e entrega](../product/GRAPH_EXPLORER.md).

## Mapa WebGL opcional — 2026-10-18

A revisão de `/grafos` troca exclusivamente o palco SVG por espaço WebGL azul profundo, esferas, névoa e halo suave de seleção. Tokens e telas aprovadas permanecem. Painel sobreposto com cabeçalho visível, folha móvel de altura inicial reduzida, legenda clicável por tipo, estilos por consenso declarado e dicas iniciais dispensáveis. Câmera percorre a seleção em vez de mover os dados. Lista e movimento reduzido continuam caminhos equivalentes. O registro de 2026-10-15 acima descreve a entrega anterior; o comportamento atual está em [GRAPH_EXPLORER](../product/GRAPH_EXPLORER.md).


Atualização de navegação em 2026-10-22: Explorar reúne Brasil Atual/Fontes/Conexões; Ideias, Propostas e Planos mantêm destinos próprios; Meu espaço reúne painel e saída. CTA Criar ideia abre a captura rápida em /painel/ideias/nova, enquanto /painel/propostas/nova prepara uma completa. Estado ativo em pill/marcador, sem sublinhado; drawer móvel agrupado e Escape/clique fora fecham os menus.
