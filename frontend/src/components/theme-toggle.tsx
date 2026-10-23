"use client";
import { useState } from "react";
import { Icon } from "./ui";

export function ThemeToggle() {
  const [selected, setSelected] = useState<"light" | "dark" | null>(null);
  return (
    <button
      className="icon-button theme-toggle"
      aria-label={
        selected
          ? `Ativar modo ${selected === "dark" ? "claro" : "escuro"}`
          : "Alternar tema claro e escuro"
      }
      title="Alternar tema"
      onClick={() => {
        const current =
          document.documentElement.dataset.theme ??
          (window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light");
        const next = current === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = next;
        setSelected(next);
        try {
          localStorage.setItem("bpt-theme", next);
        } catch {
          /* Theme works without storage. */
        }
      }}
    >
      <Icon name={selected === "dark" ? "sun" : "moon"} />
    </button>
  );
}
