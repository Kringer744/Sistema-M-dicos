import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  // arquivos estáticos servidos pelo FastAPI → desabilita otimização de imagem do Next
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
