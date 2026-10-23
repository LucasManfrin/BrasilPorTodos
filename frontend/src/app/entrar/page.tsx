import { AuthForm } from "@/features/auth/form";
export default function Login() {
  return (
    <main id="conteudo" tabIndex={-1} className="auth-page">
      <AuthForm mode="login" />
    </main>
  );
}
