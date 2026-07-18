import type { NextConfig } from "next";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

function loadRootPublicEnv() {
  const rootEnv = resolve(process.cwd(), "..", ".env");
  if (!existsSync(rootEnv)) return;

  const lines = readFileSync(rootEnv, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const separator = trimmed.indexOf("=");
    if (separator === -1) continue;

    const key = trimmed.slice(0, separator).trim();
    if (!key.startsWith("NEXT_PUBLIC_") || process.env[key]) continue;

    const rawValue = trimmed.slice(separator + 1).trim();
    process.env[key] = rawValue.replace(/^["']|["']$/g, "");
  }
}

loadRootPublicEnv();

const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;

