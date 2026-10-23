import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  ...(process.env.NEXT_OUTPUT_STANDALONE === "1"
    ? { output: "standalone", outputFileTracingRoot: path.resolve(__dirname, "..") }
    : {}),
};

export default nextConfig;
