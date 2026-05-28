"use client";
import { forwardRef, useImperativeHandle, useRef } from "react";
import SignatureCanvas from "react-signature-canvas";

export type SignatureHandle = {
  isEmpty: () => boolean;
  clear: () => void;
  toDataURL: () => string;
};

type Props = {
  height?: number;
};

const SignaturePadCard = forwardRef<SignatureHandle, Props>(function SignaturePadCard(
  { height = 220 },
  ref,
) {
  const canvasRef = useRef<SignatureCanvas | null>(null);

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
        <SignatureCanvas
          ref={canvasRef}
          penColor="#0f172a"
          canvasProps={{
            width: 600,
            height,
            className: "w-full h-full",
          }}
        />
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
