"use client";
import useSWR from "swr";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import Layout from "@/components/Layout";

type Paciente = {
  id: number;
  nome: string;
  telefone: string;
  email: string | null;
  status: string;
  origem: string;
};

const fetcher = (url: string) => api<Paciente[]>(url);

export default function PacientesPage() {
  const [q, setQ] = useState("");
  const { data, isLoading } = useSWR(`/pacientes?q=${encodeURIComponent(q)}`, fetcher);

  return (
    <Layout>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Pacientes</h1>
        <Link
          href="/pacientes/novo"
          className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          + Novo paciente (com assinatura)
        </Link>
      </div>
      <input
        placeholder="buscar por nome ou telefone..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="border rounded px-3 py-2 w-full max-w-md mb-4"
      />
      <div className="bg-white rounded shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-4 py-2">Nome</th>
              <th className="px-4 py-2">Telefone</th>
              <th className="px-4 py-2">E-mail</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Origem</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="px-4 py-2">{p.nome}</td>
                <td className="px-4 py-2">{p.telefone}</td>
                <td className="px-4 py-2">{p.email}</td>
                <td className="px-4 py-2">{p.status}</td>
                <td className="px-4 py-2">{p.origem}</td>
              </tr>
            ))}
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-4 text-center">
                  Carregando...
                </td>
              </tr>
            )}
            {data && data.length === 0 && !isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  Nenhum paciente ainda.{" "}
                  <Link href="/pacientes/novo" className="text-primary underline">
                    Cadastrar o primeiro
                  </Link>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
