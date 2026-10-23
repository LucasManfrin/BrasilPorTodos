"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { useAuth } from "./provider";
export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { signIn } = useAuth(),
    router = useRouter(),
    register = mode === "register";
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [show, setShow] = useState(false),
    [password, setPassword] = useState(""),
    [username, setUsername] = useState(""),
    [available, setAvailable] = useState("");
  useEffect(() => {
    if (!register || !/^[a-z0-9_]{3,50}$/.test(username)) return;
    let active = true;
    const timer = setTimeout(() => {
      fetchApi<{ available: boolean }>(
        `auth/username-availability?username=${encodeURIComponent(username)}`,
      )
        .then((r) => {
          if (active)
            setAvailable(
              r.data.available
                ? "Esse nome está disponível."
                : "Esse nome já está em uso.",
            );
        })
        .catch(() => {
          if (active)
            setAvailable("Disponibilidade será conferida ao criar a conta.");
        });
    }, 650);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [register, username]);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await signIn(
        mode,
        Object.fromEntries(new FormData(event.currentTarget)) as Record<
          string,
          string
        >,
      );
      const next = new URLSearchParams(window.location.search).get("next");
      router.push(
        next?.startsWith("/painel") && !next.includes("\\") ? next : "/painel",
      );
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Não deu para entrar. Tente de novo.",
      );
    } finally {
      setBusy(false);
    }
  }
  const strength =
    password.length >= 16
      ? 3
      : password.length >= 12
        ? 2
        : password.length
          ? 1
          : 0;
  return (
    <div className="auth-split">
      <div className="auth-form-side">
        <form className="form auth-form" onSubmit={submit}>
          <h1>{register ? "Sua ideia merece espaço." : "Vamos continuar?"}</h1>
          <p>
            {register
              ? "Crie uma conta para escrever. Ler continua aberto para todo mundo."
              : "Entre para cuidar das suas propostas e planos."}
          </p>
          {register && (
            <>
              <label>
                Seu nome
                <input
                  name="name"
                  autoComplete="name"
                  autoFocus
                  required
                  maxLength={120}
                  placeholder="Como você quer ser chamado?"
                />
              </label>
              <label>
                Seu @usuario
                <input
                  name="username"
                  required
                  minLength={3}
                  maxLength={50}
                  pattern="[a-z0-9_]+"
                  autoComplete="username"
                  placeholder="ex.: lucas_silva"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    setAvailable("");
                  }}
                  aria-describedby="username-hint"
                />
                <small id="username-hint" role="status">
                  {available ||
                    "A partir de 3 letras minúsculas, números ou underscore."}
                </small>
              </label>
            </>
          )}
          <label>
            E-mail
            <input
              name="email"
              type="email"
              autoComplete="email"
              autoFocus={!register}
              required
              maxLength={255}
              placeholder="voce@exemplo.com"
            />
          </label>
          <label htmlFor="auth-password">Senha</label>
          <div className="password-field">
            <input
              id="auth-password"
              name="password"
              type={show ? "text" : "password"}
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={register ? 12 : 1}
              maxLength={128}
              placeholder={
                register ? "Uma frase longa funciona bem" : "Sua senha"
              }
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-describedby={register ? "password-hint" : undefined}
            />
            <button
              type="button"
              aria-pressed={show}
              onClick={() => setShow(!show)}
              aria-label={show ? "Ocultar senha" : "Mostrar senha"}
            >
              {show ? "Ocultar" : "Mostrar"}
            </button>
          </div>
          {register && (
            <div className="password-strength">
              <span className={`strength-${strength}`} aria-hidden="true" />
              <small id="password-hint">
                {strength === 3
                  ? "Boa extensão. Prefira uma senha única para este site."
                  : strength === 2
                    ? "Mínimo atendido. Uma senha mais longa protege melhor."
                    : "Use pelo menos 12 caracteres. Evite dados pessoais."}
              </small>
            </div>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <button className="button" disabled={busy}>
            {busy ? "Aguarde…" : register ? "Criar minha conta" : "Entrar"}
          </button>
          {register && (
            <p className="auth-terms">
              Ambiente em desenvolvimento. Os termos de contribuição e a
              política de privacidade serão publicados antes do lançamento.{" "}
              <Link href="/transparencia">Veja o que já funciona.</Link>
            </p>
          )}
          <p>
            {register ? (
              <>
                Já tem conta? <Link href="/entrar">Entre</Link>.
              </>
            ) : (
              <>
                Primeira ideia por aqui?{" "}
                <Link href="/cadastro">Crie sua conta</Link>.
              </>
            )}
          </p>
        </form>
      </div>
      <aside className="auth-brand-panel">
        <span className="auth-shape" aria-hidden="true">
          <i />
        </span>
        <div>
          <h2>
            O país é grande.
            <br />
            Sua contribuição
            <br />
            também conta.
          </h2>
          <ul>
            <li>Crie propostas com fonte.</li>
            <li>Monte planos e teste a conta.</li>
            <li>Leitura sempre aberta.</li>
          </ul>
        </div>
      </aside>
    </div>
  );
}
