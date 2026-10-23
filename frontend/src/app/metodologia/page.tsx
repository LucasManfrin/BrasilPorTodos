import { PageHero } from "@/components/page-kit";
import { ReadingLayout } from "@/components/public-reading";
import Link from "next/link";
import { serverApi } from "@/lib/server-api";
import type { Guidance } from "@/features/ideas/state";
export default async function Methodology() {
  const guidance = await serverApi<Guidance>("guidance/script");
  return (
    <main id="conteudo" tabIndex={-1} className="internal-page">
      <PageHero title="Como interpretar os resultados" description="Entenda de onde vêm os números, como a conta funciona e onde ela para." tone="blue" breadcrumb="Metodologia" />
      <div className="wide-container page-body"><ReadingLayout items={[{"id": "criar-proposta", "label": "Criar uma proposta"}, {"id": "dados", "label": "Dados e escolhas"}, {"id": "referencia", "label": "Brasil de referência"}, {"id": "contextos", "label": "Contextos"}, {"id": "calculo", "label": "Cálculo fiscal"}, {"id": "sem-estimativa", "label": "Sem estimativa"}, {"id": "historico", "label": "Histórico"}, {"id": "limites", "label": "Limitações"}, {"id": "conexoes", "label": "Conexões"}]}>
      <section id="criar-proposta">
        <h2>Começar é simples. Publicar exige completar.</h2>
        <p>Uma ideia precisa de título e uma frase. Ela é privada até o autor escolher compartilhar,
          com a identificação de ideia em construção. Só uma proposta completa publicada entra em
          planos e cálculos. Salvar, compartilhar e publicar são ações distintas.</p>
        <p>Os caminhos “Me ajuda a montar” e “Eu preencho” usam o mesmo molde. “Não sei” deixa
          uma lacuna; não vira número, fonte ou ano inventado. Textos assistidos são identificados.</p>
        <h3>As mesmas perguntas, para todas as posições</h3>
        {guidance ? <><p>Roteiro público · versão {guidance.data.version}</p>
          <ol>{guidance.data.steps.map(step => <li key={step.id}>{step.question}</li>)}</ol></>
          : <p>Não conseguimos consultar o roteiro agora. Ele também está disponível no modo guiado.</p>}
        <p>A IA ajuda a transformar uma intenção informal em uma proposta mais desenvolvida. Com o
          prompt 4.0.0, apresenta uma redação principal, caminhos possíveis de implantação e
          pontos ainda indefinidos. As sugestões ficam separadas e desmarcadas: só entram no
          rascunho se você escolher e confirmar, como pontos a avaliar. Não são decisões suas
          nem efeitos comprovados. Não deve inventar números, fontes ou legislação, nem escolher
          sua posição política. As perguntas do roteiro continuam iguais. Você autoriza o envio
          da resposta e de trechos confirmados, compara o original e confere o sentido. O programa não rejeita o conteúdo por comparar palavras, números ou
          posição com seu texto. As instruções orientam a IA; você decide o que aceita. A API confere
          apenas formato e tamanho da resposta, sem certificar fatos ou neutralidade. Pode consultar o registro privado
          da chamada no editor. Sem chave, o guia usa suas palavras, sem modelo.</p>
        <h3>Documentação não é comprovação</h3>
        <p>A ordem padrão prioriza propostas completas por presença de fontes (1 ponto),
          financiamento definido (1 ponto) e revisão independente (1 ponto, ainda não atribuída
          às propostas). Revisão não avaliada vale zero, sem fingir aprovação humana.
          Empates usam recência; versões legadas continuam acessíveis, fora desse novo ranking.
          O método DOC_COMPLETENESS1 não mede popularidade, verdade ou mérito político.</p>
        <h3>Faixa de cenários declarados</h3>
        <p>DECLARED_SENSITIVITY_1 aplica multiplicadores escolhidos pela pessoa às parcelas de
          uma proposta completa publicada. O ponto inicial é 100% em todos os controles, sem
          inventar variação. O saldo menor usa custos maiores e ganhos menores; o maior faz
          o inverso. O motor fiscal usa Decimal e arredonda cada parcela para centavos.</p>
        <p>Não é probabilidade nem confiança estatística. Custos e ganhos continuam estimativas
          declaradas. Ausência de valores ou recortes fiscais incompletos/misturados bloqueiam
          a faixa. Financiamento não é contado duas vezes, e essa análise não projeta emprego,
          PIB ou efeitos do grafo.</p>
        <Link href="/painel/ideias/nova">Começar uma ideia →</Link>
      </section>
      <section id="dados">
        <h2>Dados, estimativas e escolhas</h2>
        <p>
          Dados observados vêm de uma fonte identificada, com unidade e data.
          Estimativas dependem de hipóteses. Propostas são escolhas de política
          pública que devem explicitar seus argumentos.
        </p>
      </section>
      <section id="referencia">
        <h2>De qual Brasil estamos partindo?</h2>
        <p>
          Novas propostas e planos guardam os últimos indicadores disponíveis
          quando o rascunho é criado. Cada número mantém sua fonte e período.
          Depois de publicar, essa base fica preservada, mesmo que a fonte
          divulgue uma revisão.
        </p>
        <p>
          A referência fiscal usa receitas líquidas, despesas primárias e
          resultado primário do Governo Central, nos 12 meses do mesmo ano
          fechado, pelo critério de caixa e em reais nominais. Quando a série
          está incompleta, a conta anual fica indisponível; ausência não é zero.
          Estados e municípios não fazem parte desse recorte.
        </p>
        <p>
          Mostramos o resultado publicado e a diferença em relação à receita
          líquida menos a despesa primária, sem substituir o número da fonte.
          Essa conta observada não prevê anos futuros e não é somada
          automaticamente às propostas. Combinar medidas com premissas futuras
          exige declarar um cenário e conferir recortes compatíveis.
        </p>
        <p>
          O percentual do PIB só aparece quando temos os quatro trimestres do
          PIB nominal nacional do mesmo ano, nas Contas Nacionais Trimestrais do
          IBGE. Essa soma é sujeita a revisão e não é a divulgação anual definitiva
          do Sistema de Contas Nacionais. A fonte informa valores com precisão
          de 0,01 milhão de reais (R$ 10 mil). O denominador nacional não amplia
          o recorte fiscal do Governo Central; PIB ausente não vira zero.
        </p>
      </section>
      <section>
        <h2 id="contextos">O número mudou. Mas por quê?</h2>
        <p>
          Uma comparação mostra uma mudança; sozinha, não explica a causa. Para
          discutir desemprego, por exemplo, também precisamos olhar ocupação,
          participação, informalidade e renda. Uma taxa menor pode acompanhar
          mais gente trabalhando ou menos gente procurando trabalho.
        </p>
        <p>
          Separe o dado observado, a hipótese sobre o motivo e a consequência
          esperada. Cite as evidências, apresente outras explicações possíveis e
          confira se os períodos são comparáveis. Análise por IA ainda não está
          disponível.
        </p>
        <p>
          Contextos guardam a observação exata, as fontes e seus períodos. Cada
          hipótese declara se a evidência apoia, questiona ou apenas contextualiza
          o argumento. Consequências observadas ficam separadas das projetadas,
          que precisam de premissas e limites.
        </p>
        <p>
          O autor salva privadamente. Outro administrador confere referências,
          recortes, alternativas e limitações; só depois o autor pode publicar.
          Essa revisão verifica o argumento apresentado, sem certificar causa e
          efeito. Uma edição exige nova revisão; a publicação anterior fica
          preservada mesmo quando os indicadores mudam. Contextos não alimentam
          automaticamente a simulação fiscal nem geram coeficientes.
        </p>
        <p><Link href="/contextos">Ler os contextos publicados →</Link></p>
      </section>
      <section id="calculo">
        <h2>Cálculo fiscal por ano</h2>
        <p className="formula">
          Economias + novas receitas − novas despesas − reduções de receita
        </p>
        <p>
          O total do plano soma os impactos anuais cadastrados de suas propostas
          habilitadas. É um efeito incremental, sem prever o orçamento total do
          país, o PIB ou a trajetória da dívida. Valores positivos melhoram o
          saldo; negativos o reduzem.
        </p>
        <p>
          Os valores seguem os preços declarados pelo autor: nominais do ano
          informado ou constantes de um ano-base. Não há correção automática.
          Recortes misturados ou não informados impedem interpretar o somatório
          como uma conta fiscal comparável. Uma declaração de financiamento não
          entra no cálculo novamente como receita.
        </p>
        <p>
          Novas execuções preservam uma avaliação separada dos recortes de
          governo, ano, período, contabilidade, preços e juros. Coincidir com a
          referência histórica não comprova a estimativa. A base não é somada
          às medidas. Execuções anteriores continuam sem essa avaliação.
        </p>
        <p>
          O autor pode optar por um cenário futuro declarado no plano, informando
          receita, despesa, justificativas e fontes por ano. O recorte é Governo
          Central, caixa, preços nominais, anos inteiros e conta primária sem
          juros. Não repetimos o passado nem aplicamos crescimento automático.
          Antes de combinar, o autor confirma que as propostas selecionadas ainda
          não estão incluídas nessas premissas. Alterar cenário, composição,
          período ou referência exige nova revisão. Valores ausentes e
          combinações bloqueadas não viram zero; essa confirmação humana não
          comprova a qualidade da estimativa.
        </p>
      </section>
      <section id="sem-estimativa">
        <h2>Ausência de estimativa</h2>
        <p>
          Uma proposta sem estimativa não significa custo zero. O resultado é
          marcado como parcial e identifica essa ausência. Impactos fora do
          período do plano são excluídos e sinalizados.
        </p>
      </section>
      <section id="historico">
        <h2>Histórico preservado</h2>
        <p>
          Publicar congela uma versão. Planos guardam versões específicas das
          propostas, os dados usados na execução e a versão do motor. Uma edição
          posterior não reescreve o plano anterior.
        </p>
      </section>
      <section id="limites">
        <h2>Limitações</h2>
        <p>
          A soma não detecta automaticamente todas as sobreposições entre
          medidas. Não modela inflação futura, comportamento dos contribuintes,
          crescimento, juros, emprego, distribuição de renda ou viabilidade
          jurídica.
        </p>
        <p>
          As fontes permitem investigar as afirmações; sua presença não
          constitui endosso ou revisão técnica automática.
        </p>
      </section>
      <section id="conexoes">
        <h2>O que liga uma ideia à outra?</h2>
        <p>O mapa de conexões mostra relações propostas, suas fontes, condições,
          contrapontos e revisão. A direção de uma linha é uma alegação que precisa
          ser conferida. A posição dos pontos não mede importância ou certeza,
          e percorrer a rede não soma efeitos no simulador fiscal.</p>
        <Link href="/grafos">Explorar as conexões e aprender a ler o mapa →</Link>
      </section>
      <Link href="/transparencia">Código, decisões e transparência</Link>
      </ReadingLayout></div>
    </main>
  );
}
