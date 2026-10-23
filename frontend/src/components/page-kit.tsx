import Link from "next/link";
import type { ReactNode } from "react";
import { Button, Icon } from "./ui";

export function PageHero({
  title,
  description,
  tone = "blue",
  action,
  breadcrumb,
}: {
  title: string;
  description: string;
  tone?: "blue" | "yellow" | "green" | "night";
  action?: ReactNode;
  breadcrumb?: string;
}) {
  return (
    <header className={`page-hero hero-${tone}`}>
      <div className="wide-container">
        <nav className="breadcrumb" aria-label="Você está aqui">
          <Link href="/">Início</Link>
          <span aria-hidden="true">/</span>
          <span>{breadcrumb ?? title}</span>
        </nav>
        <div className="page-hero-copy">
          <div>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
          {action}
        </div>
        <span className="band-geometry" aria-hidden="true">
          <i />
        </span>
      </div>
    </header>
  );
}
export function EmptyState({
  title,
  description,
  href,
  action = "Limpar filtros",
  error = false,
}: {
  title: string;
  description: string;
  href: string;
  action?: string;
  error?: boolean;
}) {
  return (
    <section className="empty-state" role={error ? "status" : undefined}>
      <div className="empty-geometry" aria-hidden="true">
        <Icon name={error ? "layers" : "edit"} />
      </div>
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
        <Button href={href}>
          {action}
          <Icon name="arrow" />
        </Button>
      </div>
    </section>
  );
}
export function Skeleton() {
  return (
    <div
      className="skeleton-set"
      role="status"
      aria-label="Carregando conteúdo"
    >
      <span className="skeleton" />
      <span className="skeleton" />
      <span className="skeleton" />
    </div>
  );
}
export function FilterBar({
  path,
  query,
  categories = {},
  advanced = false,
  children,
}: {
  path: string;
  query: Record<string, string | undefined>;
  categories?: Record<string, string>;
  advanced?: boolean;
  children?: ReactNode;
}) {
  function categoryHref(category: string) {
    return `${path}?${new URLSearchParams(Object.fromEntries(Object.entries({ ...query, category, page: "1" }).filter(([, value]) => Boolean(value))) as Record<string, string>)}`;
  }
  return (
    <div className="filter-bar">
      <form action={path} className="filter-search">
        <label>
          <span className="sr-only">Pesquisar</span>
          <svg
            aria-hidden="true"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="10" cy="10" r="6" />
            <path d="m15 15 6 6" />
          </svg>
          <input
            type="search"
            name="q"
            defaultValue={query.q}
            maxLength={120}
            placeholder={
              path === "/brasil"
                ? "Qual número você quer entender?"
                : "Busque por título ou assunto"
            }
          />
        </label>
        {query.category && (
          <input type="hidden" name="category" value={query.category} />
        )}
        <button className="button" type="submit">
          Buscar
        </button>
        {advanced && (
          <details className="advanced-filters">
            <summary>Mais filtros</summary>
            <div className="filter-drawer">
              <label>
                Autor
                <input
                  name="author"
                  defaultValue={query.author}
                  placeholder="nome_de_usuario"
                  minLength={3}
                  maxLength={50}
                />
              </label>
              <label>
                Ano abrangido
                <input
                  name="year"
                  type="number"
                  min={1900}
                  max={2200}
                  defaultValue={query.year}
                  placeholder="2027"
                />
              </label>
              <button className="button" type="submit">
                Aplicar filtros
              </button>
            </div>
          </details>
        )}
      </form>
      {Object.keys(categories).length > 0 && (
        <nav className="category-chips" aria-label="Filtrar por categoria">
          <Link
            href={categoryHref("")}
            className={!query.category ? "selected" : ""}
            aria-current={!query.category ? "true" : undefined}
          >
            Todas
          </Link>
          {Object.entries(categories).map(([code, text]) => (
            <Link
              key={code}
              href={categoryHref(code)}
              className={query.category === code ? "selected" : ""}
              aria-current={query.category === code ? "true" : undefined}
            >
              {text}
            </Link>
          ))}
        </nav>
      )}
      {children}
    </div>
  );
}
export function Pagination({
  path,
  query,
  page,
  total,
  size = 20,
}: {
  path: string;
  query: URLSearchParams;
  page: number;
  total: number;
  size?: number;
}) {
  const href = (n: number) =>
    `${path}?${new URLSearchParams({ ...Object.fromEntries(query), page: String(n) })}`;
  return (
    <nav className="pagination" aria-label="Páginas de resultados">
      {page > 1 && <Link href={href(page - 1)}>← Anterior</Link>}
      <span>
        Página {page} · {total} resultados
      </span>
      {page * size < total && <Link href={href(page + 1)}>Próxima →</Link>}
    </nav>
  );
}
