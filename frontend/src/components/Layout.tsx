"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken, getToken } from "@/lib/api";
import { useEffect } from "react";

const NAV = [
  { href: "/agenda", label: "Agenda" },
  { href: "/pacientes", label: "Pacientes" },
  { href: "/conversas", label: "Conversas" },
  { href: "/whatsapp", label: "WhatsApp" },
  { href: "/config", label: "Config" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const path = usePathname();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  function sair() {
    clearToken();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-slate-900 text-slate-100 flex flex-col">
        <div className="p-4 text-lg font-semibold border-b border-slate-700">
          Sistema Médico
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {NAV.map((it) => (
            <Link
              key={it.href}
              href={it.href}
              className={`block px-3 py-2 rounded ${
                path?.startsWith(it.href) ? "bg-primary" : "hover:bg-slate-800"
              }`}
            >
              {it.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={sair}
          className="m-2 px-3 py-2 rounded text-sm bg-slate-800 hover:bg-slate-700"
        >
          Sair
        </button>
      </aside>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  );
}
