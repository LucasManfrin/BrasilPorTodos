import reading from "@/components/public-reading.module.css";
import { PageHero } from "@/components/page-kit";
import { ReadingLayout } from "@/components/public-reading";
import Link from "next/link";
export default function Transparency() {
  const repo = process.env.NEXT_PUBLIC_REPOSITORY_URL;
  return (
    <main id="conteudo" tabIndex={-1} className="internal-page">
      <PageHero title="Tudo às claras." description="Código aberto, decisões visíveis e limites que precisam estar na mesa." tone="night" breadcrumb="Transparencia" />
      <div className="wide-container page-body"><div className={reading.facts} aria-label="Compromissos do projeto"><div className={reading.fact}><strong>MIT</strong><p>Código e documentação com licença aberta.</p></div><div className={reading.fact}><strong>À vista</strong><p>Método, referências e limites para conferir.</p></div><div className={reading.fact}><strong>Em construção</strong><p>O estado atual, sem prometer o que falta.</p></div></div><ReadingLayout items={[{"id": "codigo", "label": "Código aberto"}, {"id": "roadmap", "label": "Roadmap"}, {"id": "fontes", "label": "Método e fontes"}, {"id": "novidades", "label": "O que já existe"}, {"id": "estado", "label": "Estado da versão"}]}>
      <section id="codigo">
        <h2>Código e contribuição</h2>
        <p>
          BrasilPorTodos é desenvolvido sob a licença MIT. Código e documentação
          podem ser usados, modificados e compartilhados conforme seus termos.
          Fontes de terceiros conservam seus próprios termos.
        </p>
        {repo ? (
          <a href={repo} target="_blank" rel="noopener noreferrer">
            Abrir o repositório público ↗
          </a>
        ) : (
          <p className="notice">
            O repositório público está em preparação. A versão atual está em
            desenvolvimento local.
          </p>
        )}
      </section>
      <section id="roadmap">
        <h2>Roadmap</h2>
        <ol>
          <li>Fundação, documentação e ambiente de desenvolvimento.</li>
          <li>
            Contas, indicadores, fontes, propostas versionadas, Planos Brasil e
            simulação fiscal.
          </li>
          <li>
            Validação, acessibilidade, segurança, qualidade de dados e operação
            antes do lançamento.
          </li>
          <li>Evolução conforme as necessidades observadas.</li>
        </ol>
      </section>
      <section id="fontes">
        <h2>Método e fontes</h2>
        <p>
          <Link href="/metodologia">Leia a metodologia</Link> e{" "}
          <Link href="/fontes">consulte as referências publicadas</Link>. As
          hipóteses são apresentadas junto às propostas e os limites junto ao
          resultado.
        </p>
      </section>
      <section id="novidades">
        <h2>Novidades da versão em desenvolvimento</h2>
        <ul>
          <li>
            Agora é possível cadastrar fontes, publicar propostas e montar
            planos.
          </li>
          <li>
            Planos exibem o resultado fiscal e mantêm as versões usadas na
            publicação.
          </li>
          <li>
            Brasil Atual reúne séries oficiais do BCB e do IBGE, com fonte,
            data, histórico e consulta diária quando o coletor está ativo.
          </li>
          <li>
            A referência fiscal do Governo Central reúne receita líquida, despesa
            primária e resultado primário do Tesouro. Só apresenta uma conta
            anual quando os 12 meses são compatíveis, com método, fontes e
            diferença de reconciliação visíveis. O saldo incremental das medidas
            permanece separado.
          </li>
          <li>
            O PIB nominal é a soma dos quatro trimestres do mesmo ano nas Contas
            Nacionais Trimestrais do IBGE, com fontes e revisões preservadas.
            Quando a série está completa, permite comparar as contas do Governo
            Central em percentual do PIB nacional. Não é uma previsão nem a
            divulgação anual definitiva; dados ausentes ficam identificados.
          </li>
          <li>
            Correções de indicadores acrescentam revisões. Novas propostas e
            planos preservam a base usada; uma atualização dos dados não
            reescreve uma publicação anterior.
          </li>
        </ul>
      </section>
      <section id="estado">
        <h2>Estado da versão</h2>
        <p>
          A plataforma está em desenvolvimento. A publicação de uma medida não
          representa endosso institucional; leia suas premissas e verifique as
          referências.
        </p>
        <p>
          Antes do lançamento público, serão concluídas a revisão de dados e a
          política de conteúdo contribuído.
        </p>
      </section>
      </ReadingLayout></div>
    </main>
  );
}
