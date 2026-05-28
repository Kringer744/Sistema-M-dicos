"use client";
/**
 * Coleta de assinatura DENTRO do painel admin (não-kiosco).
 * Secretária abre essa tela com o paciente ao lado pra assinar pelo PC/notebook.
 * Reusa o endpoint POST /checkin (upsert por telefone + dispara cadência de lembretes).
 */
import { useRef, useState } from "react";
import useSWR from "swr";
import { useRouter } from "next/navigation";
import Layout from "@/components/Layout";
import SignaturePadCard, { SignatureHandle } from "@/components/SignaturePadCard";
import { api } from "@/lib/api";

type Passo = 1 | 2 | 3 | 4;

export default function NovoPacientePage() {
  const router = useRouter();
  const sigRef = useRef<SignatureHandle | null>(null);
  const [passo, setPasso] = useState<Passo>(1);
  const [form, setForm] = useState({
    nome: "",
    telefone: "",
    email: "",
    nascimento: "",
  });
  const [slot, setSlot] = useState<string | null>(null);
  const [resultado, setResultado] = useState<{
    paciente_id: number;
    agendamento_id: number | null;
  } | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const { data: slots } = useSWR<string[]>(
    passo === 3 ? "/checkin/slots" : null,
    (u: string) => api<string[]>(u),
  );

  function validarPasso1(): boolean {
    if (!form.nome.trim()) {
      setErro("Nome é obrigatório.");
      return false;
    }
    const tel = form.telefone.replace(/\D/g, "");
    if (tel.length < 10) {
      setErro("Telefone inválido (com DDD).");
      return false;
    }
    return true;
  }

  async function enviar(agendarRetorno: boolean) {
    setErro(null);
    if (!sigRef.current || sigRef.current.isEmpty()) {
      setErro("Por favor, assine antes de continuar.");
      return;
    }
    setEnviando(true);
    try {
      const r = await api<{ paciente_id: number; agendamento_id: number | null }>("/checkin", {
        method: "POST",
        body: JSON.stringify({
          nome: form.nome,
          telefone: form.telefone,
          email: form.email || null,
          nascimento: form.nascimento || null,
          assinatura_base64: sigRef.current.toDataURL(),
          agendar_retorno: agendarRetorno,
          slot_retorno: agendarRetorno ? slot : null,
        }),
      });
      setResultado(r);
      setPasso(4);
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Novo paciente</h1>
        <button
          onClick={() => router.push("/pacientes")}
          className="text-sm text-slate-500 hover:text-slate-700"
        >
          ← voltar
        </button>
      </div>

      {/* Stepper */}
      <ol className="flex items-center mb-6 text-sm text-slate-500">
        {[1, 2, 3, 4].map((n) => (
          <li key={n} className="flex items-center">
            <span
              className={`w-7 h-7 rounded-full flex items-center justify-center font-medium ${
                passo >= n ? "bg-primary text-white" : "bg-slate-200"
              }`}
            >
              {n}
            </span>
            {n < 4 && <span className="w-10 h-px bg-slate-200 mx-2" />}
          </li>
        ))}
        <span className="ml-4 text-slate-600">
          {passo === 1 && "Dados do paciente"}
          {passo === 2 && "Termo + assinatura"}
          {passo === 3 && "Agendar retorno"}
          {passo === 4 && "Pronto!"}
        </span>
      </ol>

      <div className="bg-white rounded-xl shadow-sm p-6 max-w-2xl">
        {passo === 1 && (
          <>
            <div className="grid gap-3">
              <input
                placeholder="Nome completo *"
                value={form.nome}
                onChange={(e) => setForm({ ...form, nome: e.target.value })}
                className="border rounded-lg p-3"
                autoFocus
              />
              <input
                placeholder="Telefone com DDD (ex: 11999990000) *"
                value={form.telefone}
                onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                className="border rounded-lg p-3"
              />
              <input
                placeholder="E-mail (opcional)"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="border rounded-lg p-3"
              />
              <input
                type="date"
                value={form.nascimento}
                onChange={(e) => setForm({ ...form, nascimento: e.target.value })}
                className="border rounded-lg p-3"
              />
            </div>
            {erro && <p className="text-red-600 text-sm mt-3">{erro}</p>}
            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setErro(null);
                  if (validarPasso1()) setPasso(2);
                }}
                className="bg-primary text-white px-6 py-2 rounded-lg font-medium"
              >
                Continuar →
              </button>
            </div>
          </>
        )}

        {passo === 2 && (
          <>
            <h2 className="font-medium mb-2">Termo de consentimento (LGPD)</h2>
            <p className="text-sm text-slate-600 mb-4">
              Eu, <b>{form.nome || "paciente"}</b>, autorizo o tratamento dos meus dados
              pessoais conforme a Lei Geral de Proteção de Dados (Lei 13.709/2018) para
              fins de atendimento médico e comunicação via WhatsApp sobre minhas consultas,
              lembretes e retornos.
            </p>
            <SignaturePadCard ref={sigRef} height={240} />
            {erro && <p className="text-red-600 text-sm mt-3">{erro}</p>}
            <div className="flex justify-between mt-6">
              <button
                onClick={() => setPasso(1)}
                className="px-4 py-2 border rounded-lg"
              >
                Voltar
              </button>
              <button
                onClick={() => {
                  if (!sigRef.current || sigRef.current.isEmpty()) {
                    setErro("Por favor, assine antes de continuar.");
                    return;
                  }
                  setErro(null);
                  setPasso(3);
                }}
                className="bg-primary text-white px-6 py-2 rounded-lg font-medium"
              >
                Continuar →
              </button>
            </div>
          </>
        )}

        {passo === 3 && (
          <>
            <h2 className="font-medium mb-2">Já quer agendar o primeiro retorno?</h2>
            <p className="text-sm text-slate-600 mb-4">
              Escolha um horário ou pule. Se pular, o bot oferece pelo WhatsApp depois.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-72 overflow-auto">
              {slots?.map((s) => (
                <button
                  key={s}
                  onClick={() => setSlot(s)}
                  className={`p-2 rounded border text-left text-sm ${
                    slot === s
                      ? "bg-primary text-white border-primary"
                      : "bg-white hover:bg-slate-50"
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
              {!slots && <p className="text-slate-500 text-sm col-span-3">Carregando...</p>}
            </div>
            {erro && <p className="text-red-600 text-sm mt-3">{erro}</p>}
            <div className="flex justify-between mt-6">
              <button
                onClick={() => setPasso(2)}
                className="px-4 py-2 border rounded-lg"
                disabled={enviando}
              >
                Voltar
              </button>
              <div className="flex gap-2">
                <button
                  onClick={() => enviar(false)}
                  disabled={enviando}
                  className="px-4 py-2 border rounded-lg disabled:opacity-60"
                >
                  Pular agendamento
                </button>
                <button
                  onClick={() => enviar(true)}
                  disabled={!slot || enviando}
                  className="bg-primary text-white px-6 py-2 rounded-lg font-medium disabled:opacity-60"
                >
                  {enviando ? "Salvando..." : "Confirmar agendamento"}
                </button>
              </div>
            </div>
          </>
        )}

        {passo === 4 && resultado && (
          <div className="text-center py-8">
            <p className="text-5xl mb-3">✅</p>
            <h2 className="text-xl font-semibold mb-2">
              Tudo certo, {form.nome.split(" ")[0]}!
            </h2>
            <p className="text-slate-600 mb-2">
              Paciente <b>#{resultado.paciente_id}</b> cadastrado e assinatura armazenada.
            </p>
            <p className="text-slate-600 mb-6">
              {resultado.agendamento_id
                ? "Consulta agendada — lembretes (D-3, D-1 e dia) já programados. WhatsApp de confirmação foi enviado."
                : "Sem retorno marcado agora. O paciente já entra na régua de pós-venda quando completar o ciclo."}
            </p>
            <div className="flex gap-2 justify-center">
              <button
                onClick={() => {
                  setForm({ nome: "", telefone: "", email: "", nascimento: "" });
                  setSlot(null);
                  setResultado(null);
                  setErro(null);
                  setPasso(1);
                }}
                className="border px-4 py-2 rounded-lg"
              >
                Cadastrar outro
              </button>
              <button
                onClick={() => router.push(`/pacientes`)}
                className="bg-primary text-white px-6 py-2 rounded-lg font-medium"
              >
                Voltar pra lista
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
