import "./globals.css";
import Nav from "./components/Nav";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#0A0E14] text-[#E8EAED]">
        <Nav />
        {children}
      </body>
    </html>
  );
}