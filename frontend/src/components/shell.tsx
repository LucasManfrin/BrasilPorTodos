"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/features/auth/provider";
import { Button, Icon } from "./ui";
import { ThemeToggle } from "./theme-toggle";
import styles from "./shell.module.css";

const participation = [
  ["/ideias", "Ideias", "O começo de uma mudança"],
  ["/propostas", "Propostas", "Medidas completas, com custos e fontes"],
  ["/planos", "Planos", "Propostas que trabalham juntas"],
];
const exploration = [
  ["/brasil", "Brasil Atual", "Os números e o contexto do país"],
  ["/fontes", "Fontes", "Confira de onde vêm os dados"],
  ["/grafos", "Conexões", "Explore relações e evidências"],
];

function Chevron() {
  return <svg className={styles.chevron} width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

export function Navbar() {
  const { user, loading, signOut } = useAuth();
  const pathname = usePathname();
  const [error, setError] = useState("");
  const header = useRef<HTMLElement>(null);
  const close = () => {
    header.current?.querySelectorAll("details[open]").forEach((item) => {
      (item as HTMLDetailsElement).open = false;
    });
  };
  useEffect(() => {
    header.current?.querySelectorAll("details[open]").forEach((item) => {
      (item as HTMLDetailsElement).open = false;
    });
  }, [pathname]);
  useEffect(() => {
    const outside = (event: PointerEvent) => {
      if (event.target instanceof Node && !header.current?.contains(event.target)) close();
    };
    document.addEventListener("pointerdown", outside);
    return () => document.removeEventListener("pointerdown", outside);
  }, []);
  const active = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const leave = async () => {
    setError("");
    try {
      await signOut();
      close();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Não deu para sair. Tente de novo.");
    }
  };
  const brand = <Link className={`brand ${styles.brand}`} href="/" aria-label="BrasilPorTodos — início"><span className="brand-symbol" aria-hidden="true"><i /></span><span>Brasil<strong>PorTodos</strong></span></Link>;
  if (pathname === "/cadastro" || pathname === "/entrar")
    return <header className="site-header"><div className="header">{brand}<Link href="/">← Voltar ao site</Link></div></header>;
  const renderLinks = (items: string[][], descriptions = false) => items.map(([href, label, description]) => (
    <Link key={href} href={href} onClick={close} className={styles.navLink} aria-current={active(href) ? "page" : undefined}>
      <span>{label}</span>{descriptions && <small>{description}</small>}
    </Link>
  ));
  const account = (
    <div className={styles.account} aria-busy={loading}>
      {loading ? <span className={styles.accountLoading} aria-label="Carregando conta" /> : user ? (
        <details name="site-navigation" className={styles.accountMenu}>
          <summary className={styles.accountTrigger} data-active={active("/painel") || undefined}>Meu espaço<Chevron /></summary>
          <div className={styles.accountDropdown}>
            <p>Seu espaço de criação</p>
            <Link href="/painel" onClick={close} aria-current={active("/painel") ? "page" : undefined}>Meu painel<Icon name="arrow" /></Link>
            <button type="button" onClick={leave}>Sair da conta</button>
          </div>
        </details>
      ) : <Link href="/entrar" className={styles.signIn} onClick={close}>Entrar</Link>}
    </div>
  );
  return (
    <>
      <header ref={header} className={`site-header ${styles.siteHeader}`} onKeyDown={(event) => {
        if (event.key !== "Escape") return;
        const opened = (event.target as HTMLElement).closest("details[open]") as HTMLDetailsElement | null;
        if (opened) {
          opened.open = false;
          opened.querySelector("summary")?.focus();
          event.stopPropagation();
        }
      }}>
        <div className={`header ${styles.header}`}>
          {brand}
          <nav className={`desktop-nav ${styles.desktopNav}`} aria-label="Navegação principal">
            <details name="site-navigation" className={styles.explore}>
              <summary className={styles.exploreTrigger} data-active={exploration.some(([href]) => active(href)) || undefined}>Explorar<Chevron /></summary>
              <div className={styles.exploreDropdown}>{renderLinks(exploration, true)}</div>
            </details>
            <span className={styles.divider} aria-hidden="true" />
            {renderLinks(participation)}
          </nav>
          <div className={styles.tools}>
            <div className={styles.desktopAccount}>{account}</div>
            <ThemeToggle />
            <Button href="/painel/ideias/nova" className={styles.cta} aria-label="Criar ideia"><span>Criar ideia</span><Icon name="edit" /></Button>
            <details name="site-navigation" className={styles.mobileMenu}>
              <summary aria-label="Abrir menu de navegação"><Icon name="menu" /></summary>
              <nav className={styles.mobileDrawer} aria-label="Menu do celular">
                <p className={styles.drawerTitle}>O que você quer explorar?</p>
                <div className={styles.mobileGroup}><span>Conhecer o país</span>{renderLinks(exploration)}</div>
                <div className={styles.mobileGroup}><span>Construir junto</span>{renderLinks(participation, true)}</div>
                <div className={styles.mobilePersonal} aria-busy={loading}>
                  {loading ? <span>Carregando conta…</span> : user ? <><Link href="/painel" onClick={close} aria-current={active("/painel") ? "page" : undefined}>Meu painel<Icon name="arrow" /></Link><button type="button" onClick={leave}>Sair da conta</button></> : <Link href="/entrar" onClick={close}>Entrar na minha conta<Icon name="arrow" /></Link>}
                </div>
                <div className={styles.mobileAbout}><Link href="/metodologia" onClick={close}>Metodologia</Link><Link href="/transparencia" onClick={close}>Transparência</Link></div>
              </nav>
            </details>
          </div>
        </div>
      </header>
      {error && <p className="shell-error error" role="alert">{error}</p>}
    </>
  );
}
export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const authPage = pathname === "/cadastro" || pathname === "/entrar";
  const repo = process.env.NEXT_PUBLIC_REPOSITORY_URL;
  const contact = process.env.NEXT_PUBLIC_CONTACT_EMAIL;
  return (
    <>
      <Navbar />
      {children}
      {!authPage && (
        <footer className="site-footer">
          <div className="wide-container footer-grid">
            <div>
              <Link className="footer-brand" href="/">
                BrasilPorTodos<span>.</span>
              </Link>
              <p>
                Entender o país é trabalho coletivo.
                <br />
                Vamos deixar as escolhas mais claras.
              </p>
              <small>Código e documentação autoral sob MIT.</small>
            </div>
            <nav aria-label="Informações do projeto">
              <Link href="/metodologia">Metodologia</Link>
              <Link href="/transparencia">Transparência</Link>
              <Link href="/fontes">Fontes dos dados</Link>
              <Link href="/grafos">Mapa de conexões</Link>
              <a
                href={repo || "/transparencia"}
                {...(repo
                  ? { target: "_blank", rel: "noopener noreferrer" }
                  : {})}
              >
                Código aberto <Icon name="arrow" />
              </a>
            </nav>
            <div className="footer-contact">
              <strong>Quer somar?</strong>
              <p>
                Ideias, correções e contribuições ajudam o projeto a crescer.
              </p>
              {contact ? (
                <a href={`mailto:${contact}`}>
                  Entre em contato <Icon name="arrow" />
                </a>
              ) : (
                <p className="muted">
                  O canal público de contato está em preparação.
                </p>
              )}
            </div>
            <p className="footer-note">
              Ferramenta independente de simulação. Sem vínculo com partidos ou
              candidaturas. Resultados dependem das premissas.
            </p>
          </div>
        </footer>
      )}
    </>
  );
}
