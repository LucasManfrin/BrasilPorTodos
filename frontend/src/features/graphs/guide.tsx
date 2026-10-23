"use client";

import Link from "next/link";
import { useId, useState } from "react";
import styles from "./guide.module.css";

const steps = [
  {
    title: "Comece pelos pontos.",
    label: "O que está conectado",
    text: "Cada ponto é um nó: uma medida, um indicador, um mecanismo ou um grupo afetado. O nome é o começo. A definição conta exatamente o que aquele ponto representa.",
    note: "Neste exemplo fictício, o Programa Alfa é uma medida. As vagas oferecidas representam uma dimensão do serviço.",
  },
  {
    title: "Leia a ligação inteira.",
    label: "O que a seta afirma",
    text: "A linha é uma aresta: uma afirmação sobre como uma coisa pode afetar outra, em certas condições. A seta mostra a origem e o destino. O sentido diz se o destino aumentaria, diminuiria ou se isso é incerto.",
    note: "Para medidas, leia: “se essa medida for adotada”. Nos outros nós, leia: “se essa dimensão aumentar”. Não inverta o sentido só porque o texto fala em uma redução.",
  },
  {
    title: "A pergunta é: com base em quê?",
    label: "O que sustenta a ligação",
    text: "Abra a relação para ver fontes, trechos, premissas, prazo e contrapontos. A revisão registra uma conferência; não transforma a afirmação em verdade. Relações em disputa continuam identificadas.",
    note: "Aqui não há evidência real: é só um desenho para aprender a ler a rede. Uma relação real precisa de fonte e revisão antes de aparecer como publicada.",
  },
] as const;

export function GraphGuide() {
  const [step, setStep] = useState(0);
  const diagramId = useId();
  const active = steps[step];

  return (
    <section className={styles.guide} id="como-funciona" aria-labelledby="graph-guide-title">
      <div className={styles.container}>
        <div className={styles.intro}>
          <h2 id="graph-guide-title">Uma decisão nunca vem sozinha.</h2>
          <p>A rede ajuda a abrir as conexões. Cada ligação tem uma explicação, condições e limites. Aprenda a ler sem precisar falar “grafo”.</p>
        </div>

        <div className={styles.lesson}>
          <ol className={styles.steps} aria-label="Passos para entender a rede">
            {steps.map((item, index) => (
              <li key={item.label}>
                <button type="button" onClick={() => setStep(index)} aria-pressed={step === index} aria-controls={`${diagramId}-lesson`}>
                  <span className={styles.stepNumber} aria-hidden="true">{index + 1}</span>
                  <span>{item.label}</span>
                  <span aria-hidden="true">↗</span>
                </button>
              </li>
            ))}
          </ol>

          <div className={styles.stage}>
            <div className={styles.stageLabel}><span>Exemplo fictício</span><span>3 nós · 2 relações</span></div>
            <figure className={styles.diagram}>
              <svg className={styles.desktopDiagram} viewBox="0 0 740 290" aria-hidden="true" focusable="false">
                <defs>
                  <marker id={`${diagramId}-arrow`} markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M 0 0 L 7 4 L 0 8" fill="none" stroke="currentColor" strokeWidth="1.5" /></marker>
                </defs>
                <g className={step === 1 ? styles.activeEdges : styles.edges}>
                  <path d="M 137 157 C 206 157 218 112 294 112" markerEnd={`url(#${diagramId}-arrow)`} />
                  <path d="M 379 112 C 452 112 465 178 536 178" markerEnd={`url(#${diagramId}-arrow)`} strokeDasharray="6 7" />
                </g>
                <g className={styles.diagramWords}>
                  <text x="215" y="108" textAnchor="middle">aumenta*</text>
                  <text x="462" y="124" textAnchor="middle">incerto</text>
                </g>
                <g className={step === 0 ? styles.activeNodes : styles.nodes}>
                  <rect x="65" y="121" width="72" height="72" rx="18" transform="rotate(-12 101 157)" />
                  <circle cx="336" cy="112" r="43" />
                  <path d="M 580 132 L 626 178 L 580 224 L 534 178 Z" />
                </g>
                <g className={styles.nodeNames} textAnchor="middle">
                  <text x="101" y="231">Programa Alfa</text>
                  <text x="336" y="190">Vagas oferecidas</text>
                  <text x="580" y="263">Acesso ao serviço</text>
                </g>
                <g className={styles.nodeSymbols} textAnchor="middle" dominantBaseline="middle"><text x="101" y="157">M</text><text x="336" y="112">I</text><text x="580" y="178">I</text></g>
              </svg>
              <svg className={styles.mobileDiagram} viewBox="0 0 360 355" aria-hidden="true" focusable="false">
                <defs><marker id={`${diagramId}-mobile-arrow`} markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M 0 0 L 7 4 L 0 8" fill="none" stroke="currentColor" strokeWidth="1.5" /></marker></defs>
                <g className={step === 1 ? styles.activeEdges : styles.edges}>
                  <path d="M 107 65 C 187 32 190 125 239 139" markerEnd={`url(#${diagramId}-mobile-arrow)`} />
                  <path d="M 249 183 C 225 235 158 215 111 265" markerEnd={`url(#${diagramId}-mobile-arrow)`} strokeDasharray="6 7" />
                </g>
                <g className={styles.diagramWords} textAnchor="middle"><text x="205" y="59">aumenta*</text><text x="196" y="249">incerto</text></g>
                <g className={step === 0 ? styles.activeNodes : styles.nodes}>
                  <rect x="42" y="39" width="64" height="64" rx="16" transform="rotate(-12 74 71)" />
                  <circle cx="268" cy="151" r="35" />
                  <path d="M 83 245 L 120 282 L 83 319 L 46 282 Z" />
                </g>
                <g className={styles.nodeSymbols} textAnchor="middle" dominantBaseline="middle"><text x="74" y="71">M</text><text x="268" y="151">I</text><text x="83" y="282">I</text></g>
                <g className={styles.nodeNames} textAnchor="middle"><text x="79" y="135">Programa Alfa</text><text x="261" y="211">Vagas oferecidas</text><text x="112" y="349">Acesso ao serviço</text></g>
              </svg>
              <figcaption>M: medida · I: indicador. *Hipótese fictícia: adotar o Programa Alfa aumentaria as vagas, se houver equipe. O efeito no acesso permanece incerto.</figcaption>
            </figure>
            <div className={styles.lessonCopy} id={`${diagramId}-lesson`} aria-live="polite" aria-atomic="true">
              <span className={styles.progress}>Passo {step + 1} de {steps.length}</span>
              <h3>{active.title}</h3>
              <p>{active.text}</p>
              <p className={styles.note}>{active.note}</p>
            </div>
          </div>
        </div>

        <div className={styles.limits}>
          <div className={styles.bigStatement}>
            <span aria-hidden="true">≠</span>
            <h3>Estar perto no desenho<br />não prova uma causa.</h3>
          </div>
          <div className={styles.reading}>
            <p>A posição dos pontos organiza a leitura. O que conta é o conteúdo da ligação e a evidência que você pode abrir.</p>
            <details>
              <summary>Três tipos de efeito. Nenhum número automático.</summary>
              <dl>
                <div><dt>Direto contábil</dt><dd>Descreve uma relação de conta declarada, no recorte informado.</dd></div>
                <div><dt>Indireto estimado</dt><dd>Depende de um caminho de efeitos e das premissas declaradas.</dd></div>
                <div><dt>Qualitativo</dt><dd>Descreve uma relação sem estimar sua magnitude.</dd></div>
              </dl>
              <p>Nesta versão, nenhum desses rótulos fornece um coeficiente. Seguir uma cadeia ou encontrar um ciclo não soma impactos nem prevê emprego, renda ou PIB.</p>
            </details>
            <details>
              <summary>O que ficou de fora também precisa aparecer.</summary>
              <p>Sem ligação, há uma lacuna no conjunto publicado — não uma prova de que não existe efeito. “Contraponto não pesquisado” é diferente de “pesquisado e não encontrado”. Premissas e desconhecidos fazem parte da leitura.</p>
            </details>
            <Link href="/metodologia">Conheça a metodologia <span aria-hidden="true">↗</span></Link>
          </div>
        </div>
      </div>
    </section>
  );
}
