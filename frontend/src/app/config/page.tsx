"use client";
import useSWR from "swr";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import Layout from "@/components/Layout";

type Cfg = {
  nome_medico: string;
  dias_trabalho: Record<string, [string, string]>;
  duracao_consulta_min: number;
  intervalo_almoco: { inicio?: string; fim?: string };
  janela_dias_futuros: number;
  posvenda_dias: number;
  cadencia_lembrete: Array<{ tipo: string; texto: string }>;
};

export default function ConfigPage() {
  const { data, mutate } = useSWR("/config", (u) => api<Cfg>(u));
  const [form, setForm] = useState<Cfg | null>(null);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  if (!form) return <Layout>Carregando...</Layout>;

  async function salvar() {
    setSalvando(true);
    try {
      await api("/config", { method: "PUT", body: JSON.stringify(form) });
      await mutate();
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Layout>
      <h1 className="text-2xl font-semibold mb-4">Configurações</h1>
      <div className="bg-white p-6 rounded shadow-sm max-w-2xl space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Nome do médico</label>
          <input
            value={form.nome_medico}
            onChange={(e) => setForm({ ...form, nome_medico: e.target.value })}
            className="w-full border rounded px-3 py-2"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Duração consulta (min)</label>
            <input
              type="number"
              value={form.duracao_consulta_min}
              onChange={(e) => setForm({ ...form, duracao_consulta_min: +e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Janela slots futuros (dias)</label>
            <input
              type="number"
              value={form.janela_dias_futuros}
              onChange={(e) => setForm({ ...form, janela_dias_futuros: +e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Pós-venda — dias inativo</label>
            <input
              type="number"
              value={form.posvenda_dias}
              onChange={(e) => setForm({ ...form, posvenda_dias: +e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Cadência de lembretes</label>
          <div className="space-y-2">
            {form.cadencia_lembrete.map((it, i) => (
              <div key={i} className="flex gap-2">
                <input
                  value={it.tipo}
                  onChange={(e) => {
                    const novo = [...form.cadencia_lembrete];
                    novo[i] = { ...it, tipo: e.target.value };
                    setForm({ ...form, cadencia_lembrete: novo });
                  }}
                  className="w-24 border rounded px-2 py-1"
                />
                <input
                  value={it.texto}
                  onChange={(e) => {
                    const novo = [...form.cadencia_lembrete];
                    novo[i] = { ...it, texto: e.target.value };
                    setForm({ ...form, cadencia_lembrete: novo });
                  }}
                  className="flex-1 border rounded px-2 py-1"
                />
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Placeholders: {"{nome} {medico} {data} {hora} {dia_semana}"}
          </p>
        </div>

        <button
          onClick={salvar}
          disabled={salvando}
          className="bg-primary text-white px-5 py-2 rounded font-medium disabled:opacity-60"
        >
          {salvando ? "Salvando..." : "Salvar"}
        </button>
      </div>
    </Layout>
  );
}
