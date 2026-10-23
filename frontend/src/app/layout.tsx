import type { Metadata } from "next";
import { Bricolage_Grotesque, DM_Sans } from "next/font/google";
import "./globals.css";
import "./internal.css";
import { AuthProvider } from "@/features/auth/provider";
import { Shell } from "@/components/shell";

const display = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});
const body = DM_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});
export const metadata: Metadata = {
  title: "BrasilPorTodos — Ideias, escolhas e contas claras",
  description:
    "Entenda os números, coloque propostas na mesa e monte um plano para o Brasil. Toda escolha tem custo, limite e consequência.",
};
const themeScript = `try{var t=localStorage.getItem('bpt-theme');if(t==='dark'||t==='light')document.documentElement.dataset.theme=t}catch(e){}`;
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="pt-BR"
      className={`${display.variable} ${body.variable}`}
      data-scroll-behavior="smooth"
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a className="skip-link" href="#conteudo">
          Ir para o conteúdo
        </a>
        <AuthProvider>
          <Shell>{children}</Shell>
        </AuthProvider>
      </body>
    </html>
  );
}
