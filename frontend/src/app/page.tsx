import Link from "next/link";
import { Button, Card, Icon, Section } from "@/components/ui";
import { CountUp, HomePlayground } from "@/components/home-playground";
import { ImpactMeter } from "@/components/impact-meter";

export default function Home() {
  return (
    <main id="conteudo" tabIndex={-1} className="home">
      <Section tone="green" className="home-hero">
        <div className="hero-grid">
          <div className="hero-copy">
            <p className="hero-note">
              <span className="note-mark" aria-hidden="true" /> Um país. Muitas
              escolhas.
            </p>
            <h1>
              Ideia boa.
              <br />E a conta,
              <br />
              <span>fecha como?</span>
            </h1>
            <p className="hero-description">
              Entenda os números, coloque propostas na mesa e monte um plano
              para o Brasil. Sem precisar saber tudo de política.
            </p>
            <div className="actions">
              <Button href="/propostas">
                Explorar propostas <Icon name="arrow" />
              </Button>
              <Button href="/brasil" variant="secondary">
                Entender o Brasil
              </Button>
            </div>
            <p className="hero-footnote">
              Aberto para ler. Livre para questionar. Feito para participar.
            </p>
          </div>
          <HomePlayground />
        </div>
      </Section>
      <div className="simulation-notice">
        <div className="wide-container">
          <Icon name="chart" />
          <p>
            <strong>Simulação, com limites à vista.</strong> Os resultados
            dependem das premissas. O site não representa partido ou
            candidatura.
          </p>
          <Link href="/metodologia">
            Entenda o cálculo <Icon name="arrow" />
          </Link>
        </div>
      </div>
      <Section className="why-section" id="por-que">
        <div className="why-grid">
          <h2>
            Na eleição,
            <br />
            vem tudo
            <br />
            <span>ao mesmo tempo.</span>
          </h2>
          <div className="why-copy">
            <p>
              Número para todo lado. Promessa para todo gosto. E você tentando
              entender o que faz sentido.
            </p>
            <p>
              O BrasilPorTodos nasceu dessa dificuldade: acompanhar todos os
              dados e todas as propostas é pesado.{" "}
              <strong>Ninguém consegue entender tudo.</strong>
            </p>
            <p>
              A ideia é tornar as escolhas mais claras. Ver de onde vem o dado,
              quanto uma medida custa e o que precisa mudar para bancá-la.
              Nenhum plano entrega um mundo perfeito: cada escolha tem custo,
              limite e consequência.
            </p>
            <a className="text-link" href="#como-funciona">
              Vamos por partes <Icon name="arrow" />
            </a>
          </div>
        </div>
      </Section>
      <Section tone="blue" className="discovery-section">
        <div className="section-heading">
          <h2>
            Menos promessa solta.
            <br />
            <span>Mais escolha visível.</span>
          </h2>
          <p>
            Você não precisa aceitar uma resposta pronta. Pode abrir a fonte,
            mudar uma premissa e olhar de novo.
          </p>
        </div>
        <div className="bento-grid">
          <Link href="/brasil" className="bento bento-data">
            <span className="bento-label">
              Brasil Atual <Icon name="arrow" />
            </span>
            <h3>
              O dado vem
              <br />
              com contexto.
            </h3>
            <div className="data-art" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
            <p>
              Fonte, unidade e data. Porque um número sozinho conta só metade da
              história.
            </p>
          </Link>
          <div className="bento bento-cost">
            <span className="bento-label">Toda escolha tem efeito</span>
            <div className="big-stat">
              <CountUp value={0} />
            </div>
            <h3>
              reais aparecem
              <br />
              por mágica.
            </h3>
            <p>
              Mais gasto precisa de receita, economia ou outra forma de
              financiamento — que também traz consequências.
            </p>
          </div>
          <Link href="/planos" className="bento bento-plan">
            <span className="bento-label">
              Planos Brasil <Icon name="arrow" />
            </span>
            <h3>
              Junte ideias.
              <br />
              Veja o conjunto.
            </h3>
            <div className="plan-art" aria-hidden="true">
              <span>Educação +</span>
              <span>Saúde +</span>
              <span>Como financiar?</span>
            </div>
            <p>
              Um plano mantém as versões usadas. Editar uma proposta depois não
              muda o passado.
            </p>
          </Link>
          <Link href="/fontes" className="bento bento-source">
            <div className="big-stat">
              <CountUp value={100} suffix="%" />
            </div>
            <div>
              <h3>leitura aberta.</h3>
              <p>Consultar dados e publicações não pede login.</p>
              <span className="text-link">
                Confira as fontes <Icon name="arrow" />
              </span>
            </div>
          </Link>
        </div>
      </Section>
      <Section className="how-section" id="como-funciona">
        <div className="section-heading">
          <h2>
            Do “e se…”
            <br />
            ao “vamos ver”.
          </h2>
          <p>Comece pelo que te importa. O resto você vai conectando.</p>
        </div>
        <ol className="how-list">
          <li>
            <span className="step-index">1</span>
            <div className="step-art art-chart" aria-hidden="true">
              <Icon name="chart" />
            </div>
            <div>
              <h3>Olhe o ponto de partida.</h3>
              <p>
                Abra o Brasil Atual. Veja o que o indicador mede e quando foi
                coletado.
              </p>
            </div>
            <Link href="/brasil">
              Ver os dados <Icon name="arrow" />
            </Link>
          </li>
          <li>
            <span className="step-index">2</span>
            <div className="step-art art-edit" aria-hidden="true">
              <Icon name="edit" />
            </div>
            <div>
              <h3>Tire a ideia da frase pronta.</h3>
              <p>
                Descreva o problema, a mudança, as fontes e o impacto esperado.
                Não sabe o custo? Deixe isso explícito.
              </p>
            </div>
            <Link href="/painel/propostas/nova">
              Criar proposta <Icon name="arrow" />
            </Link>
          </li>
          <li>
            <span className="step-index">3</span>
            <div className="step-art art-layers" aria-hidden="true">
              <Icon name="layers" />
            </div>
            <div>
              <h3>Monte um plano. Teste a conta.</h3>
              <p>
                Combine propostas e confira o saldo das medidas. Leia os avisos
                antes de tirar conclusões.
              </p>
            </div>
            <Link href="/painel/planos/novo">
              Montar plano <Icon name="arrow" />
            </Link>
          </li>
        </ol>
      </Section>
      <Section tone="yellow" className="examples-section">
        <div className="section-heading">
          <h2>
            Uma ideia.
            <br />
            Várias consequências.
          </h2>
          <p>
            Exemplos fictícios para mostrar como ler uma proposta. Os valores
            não são estimativas reais nem recomendações.
          </p>
        </div>
        <div className="example-grid">
          <Card className="example-feature">
            <span className="category-tag" data-category="HEALTH">
              Saúde · Ilustrativo
            </span>
            <h3>
              Mais atendimento.
              <br />
              De onde vem o recurso?
            </h3>
            <p>
              Um exemplo de nova despesa de R$ 60 bilhões, com R$ 30 bilhões de
              receita e R$ 10 bilhões de economia.
            </p>
            <p className="muted">
              Por Equipe BrasilPorTodos · Demonstração de 1 ano
            </p>
            <ImpactMeter positive="40000000000.00" negative="60000000000.00" />
            <Button href="/propostas" variant="secondary">
              Ver propostas publicadas <Icon name="arrow" />
            </Button>
          </Card>
          <Card className="example-small">
            <span className="category-tag" data-category="EDUCATION">
              Educação · Ilustrativo
            </span>
            <h3>
              Investir mais.
              <br />
              Reorganizar também.
            </h3>
            <p>
              R$ 20 bilhões a mais em um serviço, com o mesmo valor de economia
              em outros gastos. O saldo zero não elimina os impactos dessas
              escolhas.
            </p>
            <ImpactMeter
              positive="20000000000.00"
              negative="20000000000.00"
              compact
            />
          </Card>
          <div className="example-note">
            <Icon name="layers" />
            <h3>A conta não diz tudo.</h3>
            <p>
              Uma medida pode equilibrar o saldo e ainda ter efeitos sociais,
              ambientais ou econômicos que este simulador não calcula.
            </p>
            <Link href="/metodologia" className="text-link">
              O que o modelo alcança <Icon name="arrow" />
            </Link>
          </div>
        </div>
      </Section>
      <Section tone="blue" className="join-section">
        <div>
          <h2>
            Seu olhar também
            <br />
            entra nessa conta.
          </h2>
          <p>
            Leia, questione, proponha. O projeto é aberto — inclusive o código e
            as limitações.
          </p>
        </div>
        <div className="actions">
          <Button href="/painel/propostas/nova">
            Criar minha proposta <Icon name="arrow" />
          </Button>
          <Button href="/transparencia" variant="secondary">
            Conhecer o projeto
          </Button>
        </div>
      </Section>
    </main>
  );
}
