"use client";
import useSWR from "swr";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import Layout from "@/components/Layout";

type Status = {
  instancia: string;
  existe: boolean;
  status: "connected" | "connecting" | "disconnected" | "desconhecido";
  telefone: string | null;
  qrcode: string | null;
  instance_token: string | null;
};

const corStatus: Record<Status["status"], string> = {
  connected: "bg-emerald-100 text-emerald-700",
  connecting: "bg-amber-100 text-amber-700",
  disconnected: "bg-red-100 text-red-700",
  desconhecido: "bg-slate-100 text-slate-700",
};

const labelStatus: Record<Status["status"], string> = {
  connected: "Conectado",
  connecting: "Aguardando leitura do QR…",
  disconnected: "Desconectado",
  desconhecido: "Status desconhecido",
};

export default function WhatsAppPage() {
  const [erro, setErro] = useState<string | null>(null);
  const [acaoLoading, setAcaoLoading] = useState<string | null>(null);
  const [webhookUrl, setWebhookUrl] = useState("");

  const { data: status, mutate, isLoading } = useSWR<Status>(
    "/whatsapp/status",
    (u: string) => api<Status>(u),
    {
      // Polling: rápido enquanto conecta, lento quando conectado.
      refreshInterval: (latest) =>
        latest?.status === "connecting" ? 3000 : latest?.status === "connected" ? 15000 : 5000,
    },
  );

  useEffect(() => {
    if (typeof window !== "undefined" && !webhookUrl) {
      // Sugere a URL do webhook automaticamente
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || window.location.origin;
      setWebhookUrl(`${apiUrl.replace(/\/$/, "")}/api/webhook`);
    }
  }, [webhookUrl]);

  async function acao(nome: string, path: string, method: "POST" = "POST") {
    setErro(null);
    setAcaoLoading(nome);
    try {
      await api(path, { method });
      await mutate();
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setAcaoLoading(null);
    }
  }

  async function salvarWebhook() {
    setErro(null);
    setAcaoLoading("webhook");
    try {
      await api("/whatsapp/webhook", {
        method: "POST",
        body: JSON.stringify({ url: webhookUrl }),
      });
      alert("Webhook configurado com sucesso!");
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setAcaoLoading(null);
    }
  }

  function renderQR(qr: string) {
    // Aceita tanto base64 puro quanto data:image
    const src = qr.startsWith("data:") ? qr : `data:image/png;base64,${qr}`;
    return (
      <div className="bg-white p-4 rounded-lg border inline-block">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt="QR code" className="w-72 h-72 object-contain" />
      </div>
    );
  }

  return (
    <Layout>
      <h1 className="text-2xl font-semibold mb-4">Conexão WhatsApp</h1>

      <div className="bg-white p-6 rounded-xl shadow-sm max-w-3xl space-y-6">
        {/* Status */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">Instância</p>
            <p className="font-mono text-sm">{status?.instancia || "..."}</p>
            {status?.telefone && (
              <p className="text-xs text-slate-500 mt-1">
                Número: <span className="font-mono">{status.telefone}</span>
              </p>
            )}
          </div>
          {status && (
            <span className={`px-3 py-1 rounded-full text-sm ${corStatus[status.status]}`}>
              {labelStatus[status.status]}
            </span>
          )}
        </div>

        {/* QR ou ações */}
        {isLoading && <p>Carregando status...</p>}

        {status?.status === "disconnected" && !status.qrcode && (
          <div className="text-center py-6">
            <p className="text-slate-600 mb-4">
              WhatsApp desconectado. Clique abaixo pra gerar o QR e parear.
            </p>
            <button
              onClick={() => acao("conectar", "/whatsapp/conectar")}
              disabled={acaoLoading === "conectar"}
              className="bg-primary text-white px-6 py-3 rounded-lg font-medium disabled:opacity-60"
            >
              {acaoLoading === "conectar" ? "Gerando..." : "Gerar QR code"}
            </button>
          </div>
        )}

        {status?.qrcode && status.status !== "connected" && (
          <div className="text-center py-2">
            <p className="text-slate-600 mb-3">
              Abra o WhatsApp no celular → ⋮ → <b>Aparelhos conectados</b> → <b>Conectar
                aparelho</b> e escaneie o QR abaixo.
            </p>
            {renderQR(status.qrcode)}
            <p className="text-xs text-slate-400 mt-3">O QR atualiza automaticamente.</p>
          </div>
        )}

        {status?.status === "connected" && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-emerald-800">
            ✅ WhatsApp conectado e pronto pra enviar/receber mensagens.
          </div>
        )}

        {erro && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded">
            {erro}
          </div>
        )}

        {/* Ações */}
        <div className="flex flex-wrap gap-2 pt-4 border-t">
          <button
            onClick={() => mutate()}
            className="px-4 py-2 text-sm border rounded"
          >
            Atualizar
          </button>
          <button
            onClick={() => acao("reiniciar", "/whatsapp/reiniciar")}
            disabled={!!acaoLoading}
            className="px-4 py-2 text-sm border rounded"
          >
            {acaoLoading === "reiniciar" ? "Reiniciando..." : "Reiniciar instância"}
          </button>
          {status?.status === "connected" && (
            <button
              onClick={() => {
                if (confirm("Desconectar o WhatsApp? Você terá que escanear novo QR.")) {
                  acao("desconectar", "/whatsapp/desconectar");
                }
              }}
              disabled={!!acaoLoading}
              className="px-4 py-2 text-sm border border-red-300 text-red-600 rounded"
            >
              {acaoLoading === "desconectar" ? "Desconectando..." : "Desconectar"}
            </button>
          )}
        </div>

        {/* Webhook */}
        <div className="pt-4 border-t">
          <h2 className="font-medium mb-2">Webhook</h2>
          <p className="text-xs text-slate-500 mb-3">
            O WhatsApp precisa enviar as mensagens recebidas pro nosso backend. Configure
            uma vez logo após o pareamento.
          </p>
          <div className="flex gap-2">
            <input
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="flex-1 border rounded px-3 py-2 text-sm font-mono"
              placeholder="https://seu-dominio.com/webhook"
            />
            <button
              onClick={salvarWebhook}
              disabled={acaoLoading === "webhook" || !webhookUrl}
              className="bg-primary text-white px-4 py-2 rounded font-medium disabled:opacity-60"
            >
              {acaoLoading === "webhook" ? "Salvando..." : "Salvar webhook"}
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
