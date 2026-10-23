import Link from "next/link";
import styles from "./ui.module.css";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Button({
  href,
  children,
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  href?: string;
  variant?: "primary" | "secondary" | "tertiary";
  children: ReactNode;
}) {
  const classes = `button ${variant === "secondary" ? "secondary" : variant === "tertiary" ? styles.tertiary : ""} ${className}`;
  return href ? (
    <Link className={classes} href={href} aria-label={props["aria-label"]}>
      {children}
    </Link>
  ) : (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
export function Card({
  children,
  className = "",
  category,
}: {
  children: ReactNode;
  className?: string;
  category?: string;
}) {
  return (
    <article className={`card ${className}`} data-category={category}>
      {children}
    </article>
  );
}
export function Section({
  children,
  tone = "plain",
  className = "",
  id,
}: {
  children: ReactNode;
  tone?: "plain" | "green" | "yellow" | "blue";
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={`section section-${tone} ${className}`}>
      <div className="wide-container">{children}</div>
    </section>
  );
}
export function Icon({
  name,
  className = "",
}: {
  name:
    | "arrow"
    | "chart"
    | "edit"
    | "layers"
    | "sun"
    | "moon"
    | "menu"
    | "copy"
    | "heart"
    | "comment";
  className?: string;
}) {
  const paths: Record<string, ReactNode> = {
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    chart: (
      <>
        <path d="M4 4v16h16M8 15v-4m5 4V7m5 8v-6" />
      </>
    ),
    edit: (
      <>
        <path d="m14 5 5 5M4 20l5-1L20 8l-5-5L4 14v6Z" />
        <path d="M13 20h7" />
      </>
    ),
    layers: (
      <>
        <path d="m12 3 10 6-10 6L2 9l10-6Zm-9 11 9 5 9-5M3 18l9 5 9-5" />
      </>
    ),
    sun: (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 1v2m0 18v2M1 12h2m18 0h2M4 4l2 2m12 12 2 2M4 20l2-2M18 6l2-2" />
      </>
    ),
    moon: <path d="M20 15a8 8 0 0 1-11-11A9 9 0 1 0 20 15Z" />,
    menu: <path d="M4 6h16M4 12h16M4 18h16" />,
    copy: (
      <>
        <rect x="8" y="8" width="12" height="12" rx="2" />
        <path d="M15 4H4v11" />
      </>
    ),
    heart: <path d="M12 20 4 12C-1 6 7 1 12 7c5-6 13-1 8 5l-8 8Z" />,
    comment: <path d="M4 4h16v12H9l-5 4V4Z" />,
  };
  return (
    <svg
      aria-hidden="true"
      className={`icon ${className}`}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}
