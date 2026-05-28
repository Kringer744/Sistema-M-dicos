import "./globals.css";

export const metadata = {
  title: "Sistema Médico",
  description: "Painel de gestão da clínica",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
