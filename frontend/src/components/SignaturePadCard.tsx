"use client";
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ComponentType,
} from "react";

export type SignatureHandle = {
  isEmpty: () => boolean;
  clear: () => void;
  toDataURL: () => string;
};

type Props = {
  height?: number;
};

// SignatureCanvas usa Canvas API → carrega só no browser (evita erro no static export).
type SigComp = ComponentType<{
  ref?: React.Ref<unknown>;
  penColor?: string;
  canvasProps?: Record<string, unknown>;
}>;

const SignaturePadCard = forwardRef<SignatureHandle, Props>(function SignaturePadCard(
  { height = 220 },
  ref,
) {
  const [Sig, setSig] = useState<SigComp | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const canvasRef = useRef<any>(null);

  useEffect(() => {
    let alive = true;
    import("react-signature-canvas").then((mod) => {
      if (alive) setSig(() => mod.default as unknown as SigComp);
    });
    return () => {
      alive = false;
    };
  }, []);

  useImperativeHandle(ref, () => ({
    isEmpty: () => canvasRef.current?.isEmpty() ?? true,
    clear: () => canvasRef.current?.clear(),
    toDataURL: () => canvasRef.current?.toDataURL("image/png") ?? "",
  }));

  return (
    <div>
      <div
        className="border-2 border-dashed border-slate-300 rounded-lg bg-slate-50 overflow-hidden"
        style={{ height }}
      >
        {Sig ? (
          <Sig
            ref={canvasRef}
            penColor="#0f172a"
            canvasProps={{
              width: 600,
              height,
              className: "w-full h-full",
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm">
            carregando assinatura...
          </div>
        )}
      </div>
      <div className="flex justify-between items-center mt-2">
        <p className="text-xs text-slate-500">Assine no espaço acima</p>
        <button
          type="button"
          onClick={() => canvasRef.current?.clear()}
          className="text-sm px-3 py-1 border rounded text-slate-600 hover:bg-slate-50"
        >
          Limpar
        </button>
      </div>
    </div>
  );
});

export default SignaturePadCard;
