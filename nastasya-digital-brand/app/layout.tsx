import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Настасья — сайты и digital-упаковка под заявки",
  description: "Сайты, офферы, визуал и Telegram-воронки, которые объясняют ценность продукта, вызывают доверие и ведут клиента к заявке.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
