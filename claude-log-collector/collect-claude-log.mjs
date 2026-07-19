#!/usr/bin/env node
// -----------------------------------------------------------------------------
// collect-claude-log.mjs
//
// Thu thập lịch sử chat Claude Code CỦA ĐÚNG DỰ ÁN ĐANG CHẠY và gộp vào 1 file.
// - Tự tìm nơi Claude lưu log (~/.claude/projects, hoặc $CLAUDE_CONFIG_DIR).
// - Khớp session theo trường `cwd` bên trong log (không phụ thuộc tên thư mục
//   đã mã hóa, vốn không nhất quán giữa các máy).
// - Redact (che) các đoạn chứa API key / secret trước khi ghi ra file.
//
// Chạy 1 lần, không cần cài gói nào (chỉ cần Node.js >= 18):
//     node collect-claude-log.mjs
//
// Tuỳ chọn:
//     node collect-claude-log.mjs --project "D:\path\to\project" --out log.txt
// -----------------------------------------------------------------------------

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';

function filterNewSessionRecords(records, existingSessionIds = []) {
  const existing = new Set((existingSessionIds || []).map((id) => String(id).trim()).filter(Boolean));
  const seenInCurrentRun = new Set();
  return records.filter((record) => {
    const sessionId = String(record.sessionId || '').trim();
    if (!sessionId || existing.has(sessionId) || seenInCurrentRun.has(sessionId)) return false;
    seenInCurrentRun.add(sessionId);
    return true;
  });
}

function getExistingSessionIds(outFile) {
  if (!fs.existsSync(outFile)) return [];
  try {
    const text = fs.readFileSync(outFile, 'utf8');
    return [...text.matchAll(/^# SESSION \d+: (.+)$/gm)]
      .map((m) => m[1].trim())
      .filter(Boolean);
  } catch {
    return [];
  }
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const defaultOutFile = path.resolve(scriptDir, 'claude-ai-log.txt');

function main() {
// ----------------------------- args -----------------------------------------
const args = process.argv.slice(2);
const getOpt = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};

const projectPath = path.resolve(getOpt('--project') || process.cwd());
const projectName = path.basename(projectPath) || 'project';

// ------------------- nơi Claude lưu log (tự dò) ------------------------------
const configDir = process.env.CLAUDE_CONFIG_DIR
  ? path.resolve(process.env.CLAUDE_CONFIG_DIR)
  : path.join(os.homedir(), '.claude');
const projectsRoot = path.join(configDir, 'projects');

if (!fs.existsSync(projectsRoot)) {
  console.error(`[X] Không tìm thấy thư mục log của Claude: ${projectsRoot}`);
  console.error('    Bạn đã dùng Claude Code trên máy này chưa? (mặc định: ~/.claude/projects)');
  process.exit(1);
}

const norm = (p) => (p || '').replace(/[\\/]+/g, '/').replace(/\/+$/, '').toLowerCase();
const targetNorm = norm(projectPath);

// -------------- gom secret thật từ các file .env (nếu có) --------------------
const secrets = new Set();
for (const envName of ['.env', 'backend/.env', 'frontend/.env', 'frontend/.env.local', '.env.local']) {
  const envPath = path.join(projectPath, envName);
  if (!fs.existsSync(envPath)) continue;
  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*$/);
    if (!m) continue;
    const key = m[1];
    const val = m[2].replace(/^['"]|['"]$/g, '').trim();
    if (/(KEY|SECRET|TOKEN|PASSWORD|PASSWD)/i.test(key) && val.length >= 6 && val.toLowerCase() !== 'app' && !val.startsWith('${')) {
      secrets.add(val);
    }
  }
}

// --------------------------- redaction ---------------------------------------
const keyPatterns = [
  /AIza[0-9A-Za-z_\-]{35}/g,                               // Google API key
  /AQ\.[0-9A-Za-z_\-]{30,}/g,                              // Gemini key
  /sk-ant-[0-9A-Za-z_\-]{20,}/g,                           // Anthropic key
  /sk-[0-9A-Za-z_\-]{20,}/g,                               // OpenAI-style key
  /ghp_[0-9A-Za-z]{36}/g,                                  // GitHub PAT (classic)
  /gho_[0-9A-Za-z]{36}/g,
  /github_pat_[0-9A-Za-z_]{50,}/g,                         // GitHub PAT (fine-grained)
  /AKIA[0-9A-Z]{16}/g,                                     // AWS access key id
  /xox[baprs]-[0-9A-Za-z\-]{10,}/g,                        // Slack token
  /eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}/g, // JWT
];
const assignRe = /\b(api[_-]?key|apikey|access[_-]?token|refresh[_-]?token|secret[_-]?key|client[_-]?secret|goong[_-]?api[_-]?key|gemini[_-]?api[_-]?key|google[_-]?[a-z_]*api[_-]?key|authorization|bearer)\b(\s*[:=]\s*|\s+)(["']?)([A-Za-z0-9_\-\.]{16,})\3/gi;

let redactions = 0;
function redact(text) {
  if (!text) return text;
  let t = text;
  for (const s of [...secrets].sort((a, b) => b.length - a.length)) {
    if (t.includes(s)) {
      const parts = t.split(s);
      redactions += parts.length - 1;
      t = parts.join('[REDACTED_SECRET]');
    }
  }
  for (const re of keyPatterns) {
    t = t.replace(re, () => { redactions++; return '[REDACTED_KEY]'; });
  }
  t = t.replace(assignRe, (_m, k, sep, q, _v) => { redactions++; return `${k}${sep}${q}[REDACTED]${q}`; });
  return t;
}

// --------------------- trích nội dung chat -----------------------------------
function cleanUserText(text) {
  if (!text) return '';
  return text
    .replace(/<system-reminder>[\s\S]*?<\/system-reminder>/g, '')
    .replace(/<ide_selection>[\s\S]*?<\/ide_selection>/g, '')
    .replace(/<ide_opened_file>[\s\S]*?<\/ide_opened_file>/g, '')
    .replace(/<command-name>[\s\S]*?<\/command-name>/g, '')
    .replace(/<command-message>[\s\S]*?<\/command-message>/g, '')
    .replace(/<command-args>[\s\S]*?<\/command-args>/g, '')
    .replace(/<local-command-stdout>[\s\S]*?<\/local-command-stdout>/g, '')
    .trim();
}

function extractBlocks(content, role) {
  const out = [];
  if (content == null) return out;
  if (typeof content === 'string') { out.push({ kind: 'text', text: content }); return out; }
  if (!Array.isArray(content)) return out;
  for (const b of content) {
    if (typeof b === 'string') { out.push({ kind: 'text', text: b }); continue; }
    if (!b || typeof b !== 'object') continue;
    if (b.type === 'text' && typeof b.text === 'string') out.push({ kind: 'text', text: b.text });
    else if (b.type === 'tool_use' && role === 'assistant') out.push({ kind: 'tool', text: `[dùng công cụ: ${b.name || 'unknown'}]` });
    // Bỏ qua: tool_result, thinking, image, ... (giữ log gọn, dễ đọc)
  }
  return out;
}

function renderMessage(rec) {
  const msg = rec.message;
  if (!msg) return null;
  const role = msg.role || rec.type;
  if (role !== 'user' && role !== 'assistant') return null;

  const blocks = extractBlocks(msg.content, role);
  const parts = [];
  for (const b of blocks) {
    if (b.kind === 'tool') { parts.push(b.text); continue; }
    let text = b.text;
    if (role === 'user') text = cleanUserText(text);
    text = (text || '').trim();
    if (text) parts.push(text);
  }
  const body = parts.join('\n').trim();
  if (!body) return null;

  const ts = rec.timestamp || '';
  const label = role === 'user' ? 'USER' : 'ASSISTANT';
  return `[${ts}] ${label}:\n${redact(body)}\n`;
}

// ----------- pass 1: tìm thư mục session khớp cwd của dự án ------------------
// Đọc đồng bộ ~128KB đầu file (tránh lỗi khóa file với session đang chạy) rồi
// dò trường `cwd`. cwd luôn xuất hiện ở vài dòng đầu.
function peekCwd(file) {
  let text;
  try {
    const fd = fs.openSync(file, 'r');
    try {
      const buf = Buffer.alloc(131072);
      const n = fs.readSync(fd, buf, 0, buf.length, 0);
      text = buf.subarray(0, n).toString('utf8');
    } finally {
      fs.closeSync(fd);
    }
  } catch {
    return null;
  }
  for (const line of text.split(/\r?\n/)) {
    const t = line.trim();
    if (!t.startsWith('{') || !t.endsWith('}')) continue; // bỏ dòng cuối có thể bị cắt
    try {
      const o = JSON.parse(t);
      if (o && typeof o.cwd === 'string' && o.cwd) return o.cwd;
    } catch { /* ignore malformed line */ }
  }
  return null;
}

function listJsonl(dir) {
  return fs.readdirSync(dir)
    .filter((f) => f.toLowerCase().endsWith('.jsonl'))
    .map((f) => path.join(dir, f))
    .filter((f) => { try { return fs.statSync(f).isFile(); } catch { return false; } });
}

const matchedFiles = [];
const matchedDirs = [];
for (const entry of fs.readdirSync(projectsRoot, { withFileTypes: true })) {
  if (!entry.isDirectory()) continue;
  const dir = path.join(projectsRoot, entry.name);
  const files = listJsonl(dir);
  if (files.length === 0) continue;
  // Mọi session trong cùng thư mục dùng chung cwd → dò lần lượt cho tới khi
  // đọc được cwd (file mới nhất có thể đang ghi dở / rỗng).
  files.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  let cwd = null;
  for (const f of files) {
    cwd = peekCwd(f);
    if (cwd) break;
  }
  if (norm(cwd) === targetNorm) {
    matchedDirs.push(entry.name);
    matchedFiles.push(...files);
  }
}

if (matchedFiles.length === 0) {
  console.error(`[X] Không tìm thấy log Claude nào cho dự án: ${projectPath}`);
  console.error(`    Đã quét: ${projectsRoot}`);
  console.error('    Hãy chắc bạn chạy lệnh này TỪ TRONG thư mục dự án, hoặc dùng --project "<đường dẫn>".');
  process.exit(2);
}

// ----------- pass 2: đọc đầy đủ các file khớp, dựng log ----------------------
matchedFiles.sort((a, b) => fs.statSync(a).mtimeMs - fs.statSync(b).mtimeMs);

const out = [];
out.push('='.repeat(78));
out.push('  LỊCH SỬ CỘNG TÁC VỚI CLAUDE CODE');
out.push(`  Dự án      : ${projectName}`);
out.push(`  Đường dẫn  : ${projectPath}`);
out.push(`  Nguồn log  : ${projectsRoot}`);
out.push(`  Tạo lúc    : ${new Date().toISOString()}`);
out.push('  Ghi chú    : API key/secret đã được che ([REDACTED_*]).');
out.push('='.repeat(78));
out.push('');

let sessionCount = 0;
let messageCount = 0;
const sessionEntries = [];

for (const file of matchedFiles) {
  let lines;
  try { lines = fs.readFileSync(file, 'utf8').split(/\r?\n/); } catch { continue; }

  const rendered = [];
  for (const line of lines) {
    const t = line.trim();
    if (!t.startsWith('{')) continue;
    let rec;
    try { rec = JSON.parse(t); } catch { continue; }
    if (rec.isMeta) continue;
    if (rec.type !== 'user' && rec.type !== 'assistant') continue;
    const block = renderMessage(rec);
    if (block) { rendered.push(block); messageCount++; }
  }
  if (rendered.length === 0) continue;

  sessionCount++;
  const sessionId = path.basename(file, '.jsonl');
  const started = (() => { try { return new Date(fs.statSync(file).birthtimeMs || fs.statSync(file).mtimeMs).toISOString(); } catch { return ''; } })();
  const sessionBlock = [];
  sessionBlock.push('#'.repeat(78));
  sessionBlock.push(`# SESSION ${sessionCount}: ${sessionId}`);
  sessionBlock.push(`# File: ${file}`);
  if (started) sessionBlock.push(`# Bắt đầu (mtime): ${started}`);
  sessionBlock.push('#'.repeat(78));
  sessionBlock.push('');
  sessionBlock.push(rendered.join('\n'));
  sessionBlock.push('');
  sessionEntries.push({ sessionId, content: sessionBlock.join('\n') });
  out.push(...sessionBlock);
}

out.push('='.repeat(78));
out.push(`  TỔNG KẾT: ${sessionCount} session, ${messageCount} tin nhắn, ${redactions} chỗ đã che key.`);
out.push('='.repeat(78));

const outFile = path.resolve(getOpt('--out') || defaultOutFile);
const existingSessionIds = getExistingSessionIds(outFile);
const newSessionEntries = filterNewSessionRecords(sessionEntries, existingSessionIds);

if (fs.existsSync(outFile) && newSessionEntries.length === 0) {
  console.log('----------------------------------------------------------------');
  console.log(`Không có session mới để thêm. File đã tồn tại: ${outFile}`);
  console.log('----------------------------------------------------------------');
  return;
}

if (!fs.existsSync(outFile)) {
  fs.writeFileSync(outFile, out.join('\n'), 'utf8');
} else if (newSessionEntries.length > 0) {
  fs.appendFileSync(outFile, `\n${newSessionEntries.map((entry) => entry.content).join('\n')}`, 'utf8');
}

// --------- kiểm tra an toàn: không còn secret .env nào lọt ra ----------------
const finalText = fs.readFileSync(outFile, 'utf8');
let leaks = 0;
for (const s of secrets) if (finalText.includes(s)) leaks++;

console.log('----------------------------------------------------------------');
console.log(`Thư mục log khớp : ${matchedDirs.join(', ')}`);
console.log(`Session          : ${sessionCount}`);
console.log(`Tin nhắn         : ${messageCount}`);
console.log(`Đã che key       : ${redactions}`);
console.log(`Secret .env sót  : ${leaks} ${leaks === 0 ? '(OK)' : '(!!! KIỂM TRA LẠI)'}`);
console.log(`File kết quả     : ${outFile}`);
console.log(`Session mới      : ${newSessionEntries.length}`);
console.log('----------------------------------------------------------------');
console.log('Lưu ý: file này chứa nội dung chat — hãy giữ riêng tư, đừng commit lên repo chung.');
if (leaks > 0) process.exit(3);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}

export { filterNewSessionRecords };
