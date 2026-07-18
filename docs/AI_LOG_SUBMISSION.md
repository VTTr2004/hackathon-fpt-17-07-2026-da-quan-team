# Tai lieu nop: Nhat ky cong tac AI

Tai lieu nay co the dung de dien vao muc "Nhat ky cong tac AI" cua form nop bai.

## Tom tat de dien vao form

Du an co su dung cac cong cu AI tren VS Code/CLI trong qua trinh phan tich yeu cau, thiet ke luong, review UI/UX, xay dung prototype, kiem tra code va soan tai lieu. Nhom da dong goi nhat ky cong tac AI thanh file evidence rieng, bao gom raw session logs va ban trich xuat lich su chat de BTC co the doi chieu.

File dinh kem:

```text
ai-collaboration-evidence-live.zip
```

Noi dung file dinh kem:

- `AI_COLLABORATION_REPORT.md`: tong hop nguon log, cong cu AI, thoi gian sua doi va file raw tuong ung.
- `AI_CHAT_HISTORY.md`: ban trinh bay lich su hoi dap voi AI da trich xuat tu log.
- `raw-logs/`: raw log goc cua Codex, Claude, VS Code/Copilot workspace storage va editor logs lien quan project.
- `ai-hook-events.jsonl`: log hook tu dong khi Claude hoat dong trong VS Code.
- `README.md`, `HUONG_DAN_NOP_AI_LOG.md`: mo ta cach doc va kiem chung goi evidence.

## Noi dung de dan vao truong "Nhat ky cong tac AI"

```text
Nhom co su dung AI coding assistants trong qua trinh phat trien du an, chu yeu qua Codex CLI/Codex VS Code, Claude/Claude VS Code va mot so log lien quan VS Code/Copilot workspace.

Minh chung da duoc dong goi trong file:
ai-collaboration-evidence-live.zip

Trong goi nay co:
- AI_COLLABORATION_REPORT.md: bao cao tong hop cac file log lien quan dung project.
- AI_CHAT_HISTORY.md: lich su trao doi voi AI da duoc trich xuat de doc nhanh.
- raw-logs/: raw session logs de BTC co the doi chieu.
- ai-hook-events.jsonl: log hook tu dong ghi lai hoat dong AI khi lam viec trong VS Code/Claude.

He thong gom log theo dung project path:
D:\GitHub\hackathon-fpt-17-07-2026-da-quan-team

Ngoai file zip, nhom se dinh kem anh chup man hinh VS Code/CLI co hien thi phien lam viec voi AI neu BTC yeu cau.
```

## Danh sach minh chung hien co

Goi evidence live hien tai gom:

| Nhom log | So file | Y nghia |
|---|---:|---|
| Claude CLI | 8 | Session/project logs cua Claude lien quan repo |
| Codex CLI | 13 | Session logs cua Codex co nhac dung project |
| Editor Logs (Code) | 17 | Log VS Code co nhac project path, gom extension log |
| Workspace Storage (Code) | 19 | Workspace storage tro ve dung project, gom Copilot/debug storage neu co |
| Tong | 57 | Toan bo file lien quan project duoc copy vao `raw-logs/` |

## Cach BTC co the kiem chung

1. Giai nen `ai-collaboration-evidence-live.zip`.
2. Mo `AI_COLLABORATION_REPORT.md` de xem danh sach file log, thoi gian sua doi, nguon goc va ly do duoc match.
3. Mo `AI_CHAT_HISTORY.md` de doc nhanh noi dung trao doi voi AI.
4. Neu can doi chieu, mo file tuong ung trong `raw-logs/`.
5. Neu can xem co che tu dong, xem:

```text
scripts/collect-ai-collaboration-history.ps1
.vscode/tasks.json
.claude/settings.json
```

## Anh chup man hinh nen nop kem

Nen chup them 2-3 anh:

- VS Code dang mo project va terminal/task `AI Log Watcher`.
- Man hinh Claude/Codex trong VS Code co noi dung chat voi AI.
- Thu muc `ai-collaboration-evidence/live` hien `AI_COLLABORATION_REPORT.md` va `AI_CHAT_HISTORY.md`.

Dung phim tat Windows:

```text
Win + Shift + S
```

## Luu y bao mat

Truoc khi gui file zip:

- Soat nhanh `AI_CHAT_HISTORY.md`.
- Soat nhanh mot so raw logs lon trong `raw-logs/Claude_CLI` va `raw-logs/Codex_CLI`.
- Dam bao khong co API key, password, token, cookie, private credential.
- Neu tung paste secret vao AI, can rotate secret do va can nhac redact log truoc khi nop.

## Cach tao lai goi evidence

Chay lenh sau tu thu muc goc repo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\collect-ai-collaboration-history.ps1 -OutputDir ai-collaboration-evidence\live -NoZip
Compress-Archive -Path ai-collaboration-evidence\live -DestinationPath ai-collaboration-evidence-live.zip -Force
```

## Cach bat tu dong khi lam tiep

Mo project bang VS Code. Neu VS Code hoi:

```text
Allow Automatic Tasks in Folder?
```

Chon allow. Task `AI Log Watcher` se tu refresh evidence moi 30 giay.

Voi Claude, `.claude/settings.json` da co hook `PostToolUse` va `Stop`, nen khi Claude dung tool hoac ket thuc luot, event se duoc ghi vao:

```text
ai-collaboration-evidence/live/ai-hook-events.jsonl
```
