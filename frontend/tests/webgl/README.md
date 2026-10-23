# Teste isolado do renderizador WebGL

Na raiz do repositório, depois de `npm ci`:

```sh
node frontend/tests/webgl/serve.mjs --port 8002
```

Abra `http://127.0.0.1:8002/`. O servidor aceita somente leitura, escuta somente em loopback e serve uma lista explícita de arquivos. Encerre com Ctrl+C. Nenhum processo é instalado ou configurado para iniciar automaticamente.

A página extrai e transpila a fábrica **atual** `createGraphRenderer` de `graph-canvas-3d.tsx`, com o TypeScript já instalado, e usa a mesma versão instalada do Three.js e os tokens do produto. O wrapper React, sua escolha de alternativa acessível e o fluxo público são conferidos separadamente na aplicação. Não há cópia do motor de desenho.

Os 200 nós e 500 vínculos são objetos sintéticos, com posições pré-calculadas independentes. Não passam por `spatialLayout`, não são válidos para publicação e não são enviados à API ou ao banco. O limite público continua sendo **200 nós e 400 arestas**. Não aumentar o contrato para executar este teste.

“Medir 240 desenhos” inicia uma captura explícita, sem medição automática ao abrir a página. O palco é colocado na área visível; exige pelo menos 90% de visibilidade. A fábrica chama um observador opcional **somente depois de executar `renderer.render`**. O relatório registra 240 intervalos dessas chamadas reais, após 30 desenhos de aquecimento, com média, mediana, p95, máximo e intervalos acima de 25 ms. O observador não é usado pela aplicação e não envia telemetria.

Interação por ponteiro/teclado/roda, rolagem, redimensionamento, aba oculta, palco fora da área exigida ou descarte invalidam automaticamente a captura. Após 30 segundos sem completá-la, o teste registra captura incompleta, sem publicar FPS parcial. Quadros lentos dentro de uma captura válida permanecem nas estatísticas; não são descartados para melhorar o resultado. Essa é a cadência local de submissão do renderizador: **não** mede conclusão da GPU, apresentação no monitor nem garante 60 fps em aparelhos representativos.

“Atualizar diagnóstico” lê o contador acumulado de desenhos sem mudar a cena. Para conferir o repouso: selecione “Aresta incerta”, aguarde terminar o voo da câmera, atualize o diagnóstico duas vezes e compare `renderSubmissions`. Sem giro, interação ou partículas visíveis, o contador deve permanecer estável. Uma relação com sentido definido pode continuar animando suas partículas.

Use os botões e o canvas para conferir seleção, câmera, aresta incerta, mergulho, expansão, retorno e pausa. “Descartar recursos” remove o canvas; “Recriar rede” permite verificar ciclos repetidos de montagem. Isso confirma o ciclo exposto no DOM; uma auditoria aprofundada de memória GPU exige ferramentas próprias do navegador.

O bloco de alternativas distingue preferências reais de casos sintéticos de movimento reduzido, GPU indisponível, economia de dados e dispositivo limitado. Ele testa a regra pura; não simula configurações de sistema nem substitui a conferência do fallback na aplicação.

Confira 360, 768, 1280 e 1920 px e ambos os temas. Não gravar este servidor como rota de produção, fonte, publicação ou dado real. Não há chamada de rede para serviços externos.
