/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Adicionar output: 'export' se for um site estático e o serviço de deploy esperar isso.
  // Para um servidor Next.js completo, isso não é necessário.
  // Vamos manter simples por enquanto, pois o deploy_apply_deployment type="nextjs" deve lidar com isso.
};

module.exports = nextConfig;

