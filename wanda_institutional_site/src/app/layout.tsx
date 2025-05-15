import { Inter } from "next/font/google";
import "./globals.css";
import Header from "../components/Header.tsx";
import Footer from "../components/Footer.tsx";

// Definição manual do tipo Metadata como workaround
interface Metadata {
  title?: string | { default: string; template: string; absolute: string; };
  description?: string;
  // Adicione outros campos do Metadata conforme necessário, baseando-se na documentação do Next.js
  // Exemplo: openGraph?: OpenGraph;
}

// interface OpenGraph { // Exemplo de tipo aninhado
//   title?: string;
//   description?: string;
//   images?: Array<{ url: string; alt?: string }>;
// }

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Wanda - Inteligência de Dados em Linguagem Natural",
  description: "Transforme suas perguntas em insights com Wanda. Consulte seus bancos de dados usando linguagem natural e obtenha respostas instantâneas.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} bg-gray-50 text-gray-900 flex flex-col min-h-screen`}>
        <Header />
        <main className="flex-grow">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}

