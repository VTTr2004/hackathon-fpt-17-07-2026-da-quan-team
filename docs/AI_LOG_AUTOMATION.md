# Tai lieu van hanh AI log tu dong

Tai lieu nay mo ta cach du an thu thap, luu va trinh bay nhat ky cong tac AI dung cho phan nop minh chung hackathon.

## Muc tieu

He thong AI log duoc thiet ke de:

- Chi gom log lien quan den project hien tai.
- Luu raw log de BTC co the doi chieu khi can.
- Tao ban trinh bay de doc nhanh lich su trao doi voi AI.
- Ho tro tu dong cap nhat khi lam viec trong VS Code/Claude.
- Giam viec tim thu cong trong cac thu muc nhu `.codex/sessions` hoac `.claude/projects`.

Project hien tai:

```text
D:\GitHub\hackathon-fpt-17-07-2026-da-quan-team
```

## File va thu muc chinh

```text
scripts/collect-ai-collaboration-history.ps1
.vscode/tasks.json
.claude/settings.json
ai-collaboration-evidence/live/
ai-collaboration-evidence-live.zip
```

Y nghia:

- `scripts/collect-ai-collaboration-history.ps1`: script chinh de quet, loc, copy raw log va tao report.
- `.vscode/tasks.json`: cau hinh VS Code task tu chay watcher khi mo workspace.
- `.claude/settings.json`: cau hinh Claude hook tu ghi event sau moi lan Claude dung tool hoac ket thuc luot.
- `ai-collaboration-evidence/live/`: thu muc evidence dang duoc cap nhat.
- `ai-collaboration-evidence-live.zip`: goi nop nhanh cho BTC.

## Cac nguon log duoc ho tro

Script quet best-effort cac nguon local sau:

- Codex CLI / Codex VS Code: `%USERPROFILE%\.codex\sessions`, `%USERPROFILE%\.codex\log`.
- Claude CLI / Claude VS Code: `%USERPROFILE%\.claude\projects`.
- Gemini CLI / Gemini Code Assist: `%USERPROFILE%\.gemini`, `%APPDATA%\gemini`, `%LOCALAPPDATA%\Gemini`, VS Code global storage.
- GitHub Copilot Chat: VS Code/Cursor/Windsurf workspace storage va extension logs.
- VS Code/Cursor/Windsurf editor logs co nhac duong dan project.

## Co che chi lay dung log cua project

Script khong copy toan bo log AI cua may. Mot file chi duoc xem la lien quan khi co mot trong cac dau hieu sau:

```text
D:\GitHub\hackathon-fpt-17-07-2026-da-quan-team
D:\\GitHub\\hackathon-fpt-17-07-2026-da-quan-team
hackathon-fpt-17-07-2026-da-quan-team
d--GitHub-hackathon-fpt-17-07-2026-da-quan-team
```

Voi VS Code workspace storage, script doc `workspace.json`; chi workspace tro ve dung project moi duoc copy.

Voi Claude, neu thu muc project trong `.claude/projects` co ten encode trung voi project hien tai, script copy cac file trong thu muc do.

## Cach chay thu cong

Chay tu thu muc goc repo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\collect-ai-collaboration-history.ps1
```

Lenh nay tao mot thu muc moi trong:

```text
ai-collaboration-evidence/auto-YYYYMMDD-HHMMSS/
```

Trong thu muc ket qua co:

```text
AI_COLLABORATION_REPORT.md
AI_CHAT_HISTORY.md
raw-logs/
```

## Cach cap nhat thu muc live

Neu muon ghi vao thu muc live co dinh:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\collect-ai-collaboration-history.ps1 -OutputDir ai-collaboration-evidence\live -NoZip
```

Neu muon vua chay vua tu refresh moi 30 giay:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\collect-ai-collaboration-history.ps1 -Watch -OutputDir ai-collaboration-evidence\live -NoZip
```

## Tu dong khi mo VS Code

Da co file:

```text
.vscode/tasks.json
```

Khi mo project bang VS Code, neu VS Code hoi:

```text
Allow Automatic Tasks in Folder?
```

Chon allow. Task `AI Log Watcher` se tu chay va refresh:

```text
ai-collaboration-evidence/live/AI_COLLABORATION_REPORT.md
ai-collaboration-evidence/live/AI_CHAT_HISTORY.md
```

## Tu dong khi dung Claude trong VS Code

Da co file:

```text
.claude/settings.json
```

File nay cau hinh hook:

- `PostToolUse`: chay sau moi lan Claude dung tool.
- `Stop`: chay khi Claude ket thuc mot luot.

Ket qua hook duoc append vao:

```text
ai-collaboration-evidence/live/ai-hook-events.jsonl
```

Luu y: Codex/Copilot/Gemini khong phai luc nao cung co hook project-level tuong tu Claude, nen script se quet storage/log local cua cac cong cu do theo project path.

## Ket qua hien tai

Lan quet gan nhat tao report live voi cac nhom log:

- Claude CLI: 8 file.
- Codex CLI: 13 file.
- Editor Logs (Code): 17 file.
- Workspace Storage (Code): 19 file.

Tong cong: 57 file lien quan project.

## File nop BTC

Goi nop nhanh:

```text
ai-collaboration-evidence-live.zip
```

Ben trong co:

- `AI_COLLABORATION_REPORT.md`: bao cao nguon log va danh sach file.
- `AI_CHAT_HISTORY.md`: lich su chat da trich xuat de doc nhanh.
- `ai-hook-events.jsonl`: hook event tu dong trong qua trinh lam viec.
- `raw-logs/`: raw log goc de doi chieu.
- `README.md` va `HUONG_DAN_NOP_AI_LOG.md`: huong dan cho nguoi cham/nguoi nop.

## Bao mat truoc khi nop

Can mo va soat nhanh truoc khi gui BTC:

- Khong de lo API key, token, password, cookie.
- Khong de lo noi dung rieng tu khong lien quan bai thi.
- Neu da tung paste secret vao AI, can xoa/rotate secret do truoc khi nop.
- Raw logs co the chua duong dan may local, prompt, terminal output va noi dung file du an.

## Troubleshooting

Neu khong thay Codex/Claude logs:

1. Kiem tra da chat AI trong dung workspace chua.
2. Kiem tra project path trong log co trung voi repo hien tai khong.
3. Chay lenh thu cong:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\collect-ai-collaboration-history.ps1 -OutputDir ai-collaboration-evidence\live -NoZip
```

Neu VS Code task khong tu chay:

1. Mo Command Palette.
2. Chay `Tasks: Run Task`.
3. Chon `AI Log Watcher`.

Neu Claude hook khong ghi:

1. Kiem tra `.claude/settings.json` co duong dan dung.
2. Mo Claude trong workspace goc repo.
3. Sau mot tool/Stop, xem file `ai-collaboration-evidence/live/ai-hook-events.jsonl`.
