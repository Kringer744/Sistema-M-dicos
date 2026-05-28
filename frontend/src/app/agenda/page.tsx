"use client";
import useSWR from "swr";
import { useState } from "react";
import { api } from "@/lib/api";
import Layout from "@/components/Layout";

type Ag = {
  id: number;
  paciente_id: number;
  inicio: string;
  fim: string;
  status: string;
  origem: string;
  observacoes: string | null;
};

const fetcher = (url: string) => api<Ag[]>(url);

export default function AgendaPage() {
  const [hoje] = useState(() => new Date());
  const fimSemana = new Date(hoje);
  fimSemana.setDate(hoje.getDate() + 14);

  const url = `/agendamentos?de=${hoje.toISOString()}&ate=${fimSemana.toISOString()}`;
  const { data, isLoading, mutate } = useSWR(url, fetcher);

  async function cancelar(id: number) {
    if (!confirm("Cancelar este agendamento?")) return;
    await api(`/agendamentos/${id}/cancelar`, { method: "POST" });
    mutate();
  }
  async function realizado(id: number) {
    await api(`/agendamentos/${id}/realizado`, { method: "POST" });
    mutate();
  }

  return (
    <Layout>
      <h1 className="text-2xl font-semibold mb-4">Agenda — próximos 14 dias</h1>
      {isLoading && <p>Carregando...</p>}
      <div className="space-y-2">
        {data?.map((ag) => (
          <div
            key={ag.id}
            className="bg-white rounded p-4 shadow-sm flex items-center justify-between"
          >
            <div>
              <p className="font-medium">
                {new Date(ag.inicio).toLocaleString("pt-BR", {
                  weekday: "short",
                  day: "2-digit",
                  month: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
              <p className="text-sm text-slate-500">
                Paciente #{ag.paciente_id} · {ag.status} · {ag.origem}
              </p>
            </div>
            <div className="space-x-2">
              {ag.status !== "realizado" && (
                <button
                  onClick={() => realizado(ag.id)}
                  className="text-sm px-3 py-1 bg-emerald-100 text-emerald-700 rounded"
                >
                  Marcar realizado
                </button>
              )}
              {ag.status !== "cancelado" && (
                <button
                  onClick={() => cancelar(ag.id)}
                  className="text-sm px-3 py-1 bg-red-100 text-red-700 rounded"
                >
                  Cancelar
                </button>
              )}
            </div>
          </div>
        ))}
        {data && data.length === 0 && (
          <p className="text-slate-500">Sem agendamentos no período.</p>
        )}
      </div>
    </Layout>
  );
}
