/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  // arquivos estáticos servidos pelo FastAPI → desabilita otimização de imagem
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
