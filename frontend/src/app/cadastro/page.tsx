import { AuthForm } from "@/features/auth/form";
export default function Register() {
  return (
    <main id="conteudo" tabIndex={-1} className="auth-page">
      <AuthForm mode="register" />
    </main>
  );
}
