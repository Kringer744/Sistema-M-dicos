"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

export default function SetupPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", nome: "", senha: "" });
  const [erro, setErro] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    try {
      const r = await api<{ token: string }>("/auth/setup", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setToken(r.token);
      router.replace("/agenda");
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <form onSubmit={submit} className="bg-white p-8 rounded-xl shadow w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-semibold">Criar admin</h1>
        <p className="text-xs text-slate-500">Só funciona uma vez.</p>
        <input
          placeholder="nome"
          value={form.nome}
          onChange={(e) => setForm({ ...form, nome: e.target.value })}
          className="w-full border rounded px-3 py-2"
          required
        />
        <input
          type="email"
          placeholder="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="w-full border rounded px-3 py-2"
          required
        />
        <input
          type="password"
          placeholder="senha"
          value={form.senha}
          onChange={(e) => setForm({ ...form, senha: e.target.value })}
          className="w-full border rounded px-3 py-2"
          required
        />
        {erro && <p className="text-red-600 text-sm">{erro}</p>}
        <button className="w-full bg-primary text-white rounded py-2 font-medium">Criar</button>
      </form>
    </div>
  );
}
