import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const root = path.join(projectRoot, "sample-data", "ai-cashflow-variants");

async function walk(dir) {
  const out = [];
  for (const e of await fs.readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...await walk(p));
    else if (e.name.endsWith(".xlsx")) out.push(p);
  }
  return out;
}

let failures = 0;
for (const file of await walk(root)) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(file));
  const sheets = JSON.parse((await wb.inspect({ kind: "sheet", include: "name,id" })).ndjson.split("\n")[0] || "{}");
  const errors = await wb.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "final formula error scan",
  });
  const records = errors.ndjson.trim() ? errors.ndjson.trim().split("\n").filter(Boolean).map(x => JSON.parse(x)) : [];
  const count = records.filter(x => x.kind === "match" && x.address).length;
  if (count) failures += count;
  console.log(JSON.stringify({ file: path.relative(root, file), formula_errors: count, first_sheet: sheets.name ?? null }));
}

const manifest = JSON.parse(await fs.readFile(path.join(root, "manifest.json"), "utf8"));
for (const c of manifest.cases) {
  const e = c.expected;
  const ok = e.opening_balance + e.net_cashflow === e.closing_balance && e.cash_inflow - e.cash_outflow === e.net_cashflow;
  if (!ok) failures++;
  console.log(JSON.stringify({ case: c.id, cashflow_reconciles: ok, closing_balance: e.closing_balance }));
}

if (failures) process.exit(1);
