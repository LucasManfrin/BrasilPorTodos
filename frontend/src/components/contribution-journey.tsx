import Link from "next/link";
import styles from "./contribution-journey.module.css";

const stages = {
  ideas: { name: "Ideia", href: "/ideias", title: "Uma vontade de mudar algo. Só isso já vale.", description: "Dê um título e conte sua ideia em uma frase. Pode ter dúvidas e ainda não saber custos ou fontes.", note: "Você escolhe se quer compartilhar. Ideias não entram nos cálculos nem nos planos." },
  policies: { name: "Proposta", href: "/propostas", title: "A ideia ganhou uma medida concreta.", description: "Aqui você explica o que vai fazer, quem ganha ou perde, os riscos, o financiamento e as fontes. A proposta completa é publicada com esses detalhes.", note: "Só propostas completas e publicadas podem entrar em planos. Ter campos preenchidos não comprova que a medida vai funcionar." },
  plans: { name: "Plano", href: "/planos", title: "Várias propostas. Um conjunto de escolhas.", description: "Escolha propostas completas já publicadas e veja juntas as despesas, economias e receitas declaradas. Um plano pode combinar propostas de autores diferentes.", note: "O cálculo mostra o efeito fiscal das medidas. Não é uma previsão do Brasil, e ideias soltas não entram na conta." },
};

export function ContributionJourney({ current }: { current: keyof typeof stages }) {
  const stage = stages[current];
  return <section className={styles.journey} aria-label="Entenda ideias, propostas e planos">
    <nav aria-label="Da ideia ao plano"><ol>{Object.entries(stages).map(([key, item]) => <li key={key}><Link href={item.href} aria-current={key === current ? "page" : undefined}>{item.name}</Link></li>)}</ol></nav>
    <div className={styles.explanation}><h2>{stage.title}</h2><p>{stage.description}</p><p className={styles.note}>{stage.note}</p></div>
  </section>;
}
