"use client";
/**
 * Tela do TABLET na clínica.
 * Acesso sem login (kiosco). Não usa Layout admin.
 */
import { useRef, useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import SignaturePadCard, { SignatureHandle } from "@/components/SignaturePadCard";

type SlotsResp = string[];

export default function CheckinPage() {
  const sigRef = useRef<SignatureHandle | null>(null);
  const [passo, setPasso] = useState<1 | 2 | 3 | 4>(1);
  const [form, setForm] = useState({
    nome: "",
    telefone: "",
    email: "",
    nascimento: "",
  });
  const [slot, setSlot] = useState<string | null>(null);
  const [resultado, setResultado] = useState<{ paciente_id: number; agendamento_id: number | null } | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const { data: slots } = useSWR<SlotsResp>(
    passo === 3 ? "/checkin/slots" : null,
    (u: string) => api<SlotsResp>(u),
  );

  async function finalizar(agendarRetorno: boolean) {
    setErro(null);
    try {
      if (!sigRef.current || sigRef.current.isEmpty()) {
        setErro("Por favor, assine antes de continuar.");
        return;
      }
      const assinatura = sigRef.current.toDataURL();
      const r = await api<{ paciente_id: number; agendamento_id: number | null }>("/checkin", {
        method: "POST",
        body: JSON.stringify({
          nome: form.nome,
          telefone: form.telefone,
          email: form.email || null,
          nascimento: form.nascimento || null,
          assinatura_base64: assinatura,
          agendar_retorno: agendarRetorno,
          slot_retorno: agendarRetorno ? slot : null,
        }),
      });
      setResultado(r);
      setPasso(4);
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-2xl">
        {passo === 1 && (
          <>
            <h1 className="text-3xl font-bold mb-6">Bem-vindo(a) à clínica</h1>
            <div className="space-y-3">
              <input
                placeholder="Nome completo"
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
                className="w-full border rounded-lg p-4 text-lg"
              />
              <input
                placeholder="Telefone com DDD (ex: 11999990000)"
                value={form.telefone}
                onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                className="w-full border rounded-lg p-4 text-lg"
              />
              <input
                placeholder="E-mail (opcional)"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full border rounded-lg p-4 text-lg"
              />
              <input
                type="date"
                placeholder="Nascimento"
                value={form.nascimento}
                onChange={(e) => setForm({ ...form, nascimento: e.target.value })}
                className="w-full border rounded-lg p-4 text-lg"
              />
            </div>
            <button
              onClick={() => setPasso(2)}
              disabled={!form.nome || !form.telefone}
              className="w-full mt-6 bg-primary text-white text-lg font-semibold py-4 rounded-lg disabled:opacity-50"
            >
              Continuar →
            </button>
          </>
        )}

        {passo === 2 && (
          <>
            <h1 className="text-2xl font-bold mb-2">Termo de consentimento</h1>
            <p className="text-sm text-slate-600 mb-4">
              Autorizo o tratamento dos meus dados conforme a LGPD para fins de atendimento e
              comunicação via WhatsApp sobre minhas consultas.
            </p>
            <SignaturePadCard ref={sigRef} height={260} />
            {erro && <p className="text-red-600 text-sm mt-2">{erro}</p>}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setPasso(1)}
                className="flex-1 border py-3 rounded-lg"
              >
                Voltar
              </button>
              <button
                onClick={() => setPasso(3)}
                className="flex-1 bg-primary text-white py-3 rounded-lg font-semibold"
              >
                Continuar →
              </button>
            </div>
          </>
        )}

        {passo === 3 && (
          <>
            <h1 className="text-2xl font-bold mb-2">Quer já agendar próximo retorno?</h1>
            <p className="text-sm text-slate-600 mb-4">Escolha um horário ou pule.</p>
            <div className="grid grid-cols-2 gap-2 max-h-80 overflow-auto">
              {slots?.map((s) => (
                <button
                  key={s}
                  onClick={() => setSlot(s)}
                  className={`p-3 rounded border text-left ${
                    slot === s ? "bg-primary text-white border-primary" : "bg-white"
                  }`}
                >
                  {new Date(s).toLocaleString("pt-BR", {
                    weekday: "short",
                    day: "2-digit",
                    month: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </button>
              ))}
            </div>
            {erro && <p className="text-red-600 text-sm mt-2">{erro}</p>}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => finalizar(false)}
                className="flex-1 border py-3 rounded-lg"
              >
                Pular (sem agendar)
              </button>
              <button
                onClick={() => finalizar(true)}
                disabled={!slot}
                className="flex-1 bg-primary text-white py-3 rounded-lg font-semibold disabled:opacity-50"
              >
                Confirmar agendamento
              </button>
            </div>
          </>
        )}

        {passo === 4 && resultado && (
          <div className="text-center py-12">
            <p className="text-6xl mb-4">✅</p>
            <h1 className="text-2xl font-bold mb-2">Tudo certo, {form.nome.split(" ")[0]}!</h1>
            <p className="text-slate-600">
              {resultado.agendamento_id
                ? "Sua próxima consulta está marcada. Vamos te lembrar por WhatsApp."
                : "Cadastro feito! Quando quiser agendar, mande mensagem no WhatsApp da clínica."}
            </p>
            <button
              onClick={() => {
                setForm({ nome: "", telefone: "", email: "", nascimento: "" });
                setSlot(null);
                setResultado(null);
                setPasso(1);
              }}
              className="mt-8 bg-primary text-white px-6 py-3 rounded-lg"
            >
              Próximo paciente
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
