<#
.SYNOPSIS
Collect AI collaboration history that belongs to the current project.

.DESCRIPTION
This script searches common local AI assistant log locations, keeps files that
match the target project path/name, copies raw evidence, and creates readable
Markdown reports for hackathon submission.

Supported sources are best-effort and local-only:
- Codex CLI / Codex VS Code sessions
- Claude / Claude Code / Claude VS Code project logs
- Gemini CLI and Gemini Code Assist VS Code storage
- GitHub Copilot Chat VS Code/Cursor/Windsurf workspace storage
- Generic VS Code/Cursor/Windsurf extension logs

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts\collect-ai-collaboration-history.ps1

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts\collect-ai-collaboration-history.ps1 -ProjectPath "D:\GitHub\my-project"
#>

[CmdletBinding()]
param(
    [string]$ProjectPath = (Get-Location).Path,
    [string]$OutputDir = "",
    [int]$MaxScanFileMB = 160,
    [int]$MaxTranscriptItemsPerFile = 80,
    [int]$MaxSnippetChars = 900,
    [switch]$Watch,
    [int]$WatchIntervalSeconds = 30,
    [switch]$Hook,
    [string]$Tool = "unknown",
    [switch]$InstallClaudeHook,
    [switch]$NoRawCopy,
    [switch]$NoZip
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

function Resolve-FullPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (Test-Path -LiteralPath $Path) {
        return (Resolve-Path -LiteralPath $Path).ProviderPath
    }

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Path))
}

function ConvertTo-SafeName {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "unknown"
    }

    $safe = $Value -replace '[^\w\.-]+', '_'
    $safe = $safe.Trim('_')

    if ($safe.Length -gt 96) {
        $hash = Get-StringHashPrefix -Value $safe -Length 10
        $safe = "{0}_{1}" -f $safe.Substring(0, 80), $hash
    }

    if ([string]::IsNullOrWhiteSpace($safe)) {
        return "unknown"
    }

    return $safe
}

function Get-StringHashPrefix {
    param(
        [string]$Value,
        [int]$Length = 10
    )

    $sha1 = [System.Security.Cryptography.SHA1]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
        $hashBytes = $sha1.ComputeHash($bytes)
        $hash = ([System.BitConverter]::ToString($hashBytes)).Replace('-', '').ToLowerInvariant()
        return $hash.Substring(0, [Math]::Min($Length, $hash.Length))
    }
    finally {
        $sha1.Dispose()
    }
}

function Add-UniqueValue {
    param(
        [System.Collections.ArrayList]$List,
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return
    }

    foreach ($existing in $List) {
        if ([string]::Equals($existing, $Value, [System.StringComparison]::OrdinalIgnoreCase)) {
            return
        }
    }

    [void]$List.Add($Value)
}

function Get-ProjectSearchTerms {
    param([string]$FullProjectPath)

    $terms = New-Object System.Collections.ArrayList
    $projectName = Split-Path -Leaf $FullProjectPath
    $slashPath = $FullProjectPath.Replace('\', '/')
    $escapedBackslashPath = $FullProjectPath.Replace('\', '\\')
    $claudePathName = ($FullProjectPath -replace ':', '' -replace '[\\/]', '-')

    Add-UniqueValue -List $terms -Value $FullProjectPath
    Add-UniqueValue -List $terms -Value $slashPath
    Add-UniqueValue -List $terms -Value $escapedBackslashPath
    Add-UniqueValue -List $terms -Value $projectName
    Add-UniqueValue -List $terms -Value $claudePathName
    Add-UniqueValue -List $terms -Value $claudePathName.ToLowerInvariant()

    if ($slashPath -match '^([A-Za-z]):/(.*)$') {
        $drive = $matches[1]
        $rest = $matches[2]
        Add-UniqueValue -List $terms -Value ("file:///{0}%3A/{1}" -f $drive.ToLowerInvariant(), $rest)
        Add-UniqueValue -List $terms -Value ("file:///{0}%3A/{1}" -f $drive.ToUpperInvariant(), $rest)
        Add-UniqueValue -List $terms -Value ("file:///{0}:/{1}" -f $drive.ToLowerInvariant(), $rest)
        Add-UniqueValue -List $terms -Value ("file:///{0}:/{1}" -f $drive.ToUpperInvariant(), $rest)
    }

    return @($terms)
}

function Find-FirstTerm {
    param(
        [string]$Value,
        [string[]]$Terms
    )

    if ([string]::IsNullOrEmpty($Value)) {
        return $null
    }

    foreach ($term in $Terms) {
        if ([string]::IsNullOrWhiteSpace($term)) {
            continue
        }

        if ($Value.IndexOf($term, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $term
        }
    }

    return $null
}

function Test-TextLikeFile {
    param([System.IO.FileInfo]$File)

    $textExtensions = @(
        ".jsonl", ".json", ".log", ".txt", ".md", ".markdown",
        ".yaml", ".yml", ".csv", ".tsv"
    )

    return $textExtensions -contains $File.Extension.ToLowerInvariant()
}

function Test-CopyableFile {
    param([System.IO.FileInfo]$File)

    if (Test-TextLikeFile -File $File) {
        return $true
    }

    $copyNames = @(
        "state.vscdb",
        "state.vscdb.backup",
        "state.vscdb-shm",
        "state.vscdb-wal",
        "workspace.json"
    )

    return $copyNames -contains $File.Name.ToLowerInvariant()
}

function Test-FileContentMatches {
    param(
        [System.IO.FileInfo]$File,
        [string[]]$Terms,
        [int64]$MaxBytes
    )

    if (-not (Test-TextLikeFile -File $File)) {
        return $false
    }

    if ($File.Length -gt $MaxBytes) {
        return $false
    }

    try {
        return [bool](Select-String -LiteralPath $File.FullName -Pattern $Terms -SimpleMatch -Quiet -ErrorAction SilentlyContinue)
    }
    catch {
        return $false
    }
}

function New-SearchSource {
    param(
        [string]$Tool,
        [string]$Root,
        [string]$Hint,
        [bool]$ForceInclude = $false,
        [bool]$WorkspaceStorage = $false
    )

    [pscustomobject]@{
        Tool = $Tool
        Root = $Root
        Hint = $Hint
        ForceInclude = $ForceInclude
        WorkspaceStorage = $WorkspaceStorage
    }
}

function Get-Prop {
    param(
        $Object,
        [string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }

    $prop = $Object.PSObject.Properties[$Name]
    if ($null -eq $prop) {
        return $null
    }

    return $prop.Value
}

function Convert-ContentToText {
    param($Content)

    if ($null -eq $Content) {
        return ""
    }

    if ($Content -is [string]) {
        return $Content
    }

    if ($Content -is [System.Array]) {
        $parts = New-Object System.Collections.ArrayList
        foreach ($item in $Content) {
            $text = Convert-ContentToText -Content $item
            if (-not [string]::IsNullOrWhiteSpace($text)) {
                [void]$parts.Add($text)
            }
        }
        return ($parts -join "`n")
    }

    $textProp = Get-Prop -Object $Content -Name "text"
    if ($null -ne $textProp) {
        return Convert-ContentToText -Content $textProp
    }

    $contentProp = Get-Prop -Object $Content -Name "content"
    if ($null -ne $contentProp) {
        return Convert-ContentToText -Content $contentProp
    }

    $messageProp = Get-Prop -Object $Content -Name "message"
    if ($null -ne $messageProp) {
        return Convert-ContentToText -Content $messageProp
    }

    $valueProp = Get-Prop -Object $Content -Name "value"
    if ($null -ne $valueProp) {
        return Convert-ContentToText -Content $valueProp
    }

    return ""
}

function Test-ToolOnlyContent {
    param($Content)

    if ($null -eq $Content) {
        return $false
    }

    if ($Content -is [System.Array]) {
        $hasToolContent = $false
        $hasConversationContent = $false

        foreach ($item in $Content) {
            if ($item -is [string]) {
                if (-not [string]::IsNullOrWhiteSpace($item)) {
                    $hasConversationContent = $true
                }
                continue
            }

            $type = Get-Prop -Object $item -Name "type"
            if ($type -in @("tool_result", "tool_use", "thinking")) {
                $hasToolContent = $true
                continue
            }

            if ($type -in @("text", "input_text", "output_text", "markdown")) {
                $hasConversationContent = $true
                continue
            }

            $text = Convert-ContentToText -Content $item
            if (-not [string]::IsNullOrWhiteSpace($text)) {
                $hasConversationContent = $true
            }
        }

        return ($hasToolContent -and -not $hasConversationContent)
    }

    $singleType = Get-Prop -Object $Content -Name "type"
    return ($singleType -in @("tool_result", "tool_use", "thinking"))
}

function Clean-TranscriptText {
    param([string]$Text)

    if ($null -eq $Text) {
        return ""
    }

    $clean = [System.Text.RegularExpressions.Regex]::Replace(
        $Text,
        '<ide_opened_file>.*?</ide_opened_file>\s*',
        '',
        [System.Text.RegularExpressions.RegexOptions]::Singleline
    )

    return $clean.Trim()
}

function Normalize-Role {
    param($Role)

    if ($null -eq $Role) {
        return ""
    }

    $roleText = ([string]$Role).ToLowerInvariant()
    switch ($roleText) {
        "human" { return "user" }
        "model" { return "assistant" }
        "ai" { return "assistant" }
        "bot" { return "assistant" }
        default { return $roleText }
    }
}

function Test-SkipTranscriptText {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $true
    }

    $skipMarkers = @(
        "<environment_context>",
        "<permissions instructions>",
        "<skills_instructions>",
        "<apps_instructions>",
        "<plugins_instructions>",
        "<recommended_plugins>",
        "You are Codex, a coding agent",
        "Filesystem sandboxing defines"
    )

    foreach ($marker in $skipMarkers) {
        if ($Text.IndexOf($marker, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
    }

    return $false
}

function Limit-Text {
    param(
        [string]$Text,
        [int]$MaxChars
    )

    if ($null -eq $Text) {
        return ""
    }

    $clean = ($Text -replace "\r\n", "`n").Trim()
    if ($clean.Length -le $MaxChars) {
        return $clean
    }

    return ($clean.Substring(0, $MaxChars).TrimEnd() + "`n...[truncated]")
}

function Add-TranscriptItemFromObject {
    param(
        $Object,
        [string]$SourceFile,
        [string]$Tool,
        [System.Collections.ArrayList]$Items
    )

    $role = ""
    $text = ""
    $timestamp = Get-Prop -Object $Object -Name "timestamp"

    $type = Get-Prop -Object $Object -Name "type"

    if ($type -eq "response_item") {
        $payload = Get-Prop -Object $Object -Name "payload"
        if ((Get-Prop -Object $payload -Name "type") -eq "message") {
            $role = Normalize-Role -Role (Get-Prop -Object $payload -Name "role")
            $content = Get-Prop -Object $payload -Name "content"
            if (Test-ToolOnlyContent -Content $content) {
                return
            }
            $text = Convert-ContentToText -Content $content
        }
    }

    if ([string]::IsNullOrWhiteSpace($role) -and (($type -eq "user") -or ($type -eq "assistant"))) {
        $message = Get-Prop -Object $Object -Name "message"
        if ($null -ne $message) {
            $role = Normalize-Role -Role (Get-Prop -Object $message -Name "role")
            $content = Get-Prop -Object $message -Name "content"
            if (Test-ToolOnlyContent -Content $content) {
                return
            }
            $text = Convert-ContentToText -Content $content
        }
        else {
            $role = Normalize-Role -Role $type
            $content = Get-Prop -Object $Object -Name "content"
            if (Test-ToolOnlyContent -Content $content) {
                return
            }
            $text = Convert-ContentToText -Content $content
        }
    }

    if ([string]::IsNullOrWhiteSpace($role)) {
        $role = Normalize-Role -Role (Get-Prop -Object $Object -Name "role")
        $content = Get-Prop -Object $Object -Name "content"
        if (Test-ToolOnlyContent -Content $content) {
            return
        }
        $text = Convert-ContentToText -Content $content
    }

    if (($role -ne "user") -and ($role -ne "assistant")) {
        return
    }

    $text = Clean-TranscriptText -Text $text

    if (Test-SkipTranscriptText -Text $text) {
        return
    }

    [void]$Items.Add([pscustomobject]@{
        Tool = $Tool
        SourceFile = $SourceFile
        Timestamp = [string]$timestamp
        Role = $role
        Text = $text
    })
}

function Read-JsonlTranscript {
    param(
        [System.IO.FileInfo]$File,
        [string]$Tool,
        [int]$MaxItems
    )

    $items = New-Object System.Collections.ArrayList

    try {
        foreach ($line in [System.IO.File]::ReadLines($File.FullName)) {
            if ($items.Count -ge $MaxItems) {
                break
            }

            $trimmed = $line.Trim()
            if (-not $trimmed.StartsWith("{")) {
                continue
            }

            try {
                $obj = $trimmed | ConvertFrom-Json -ErrorAction Stop
                Add-TranscriptItemFromObject -Object $obj -SourceFile $File.FullName -Tool $Tool -Items $items
            }
            catch {
                continue
            }
        }
    }
    catch {
        return @()
    }

    return @($items)
}

function Search-ObjectForMessages {
    param(
        $Value,
        [string]$SourceFile,
        [string]$Tool,
        [System.Collections.ArrayList]$Items,
        [int]$Depth,
        [int]$MaxItems
    )

    if (($null -eq $Value) -or ($Depth -gt 8) -or ($Items.Count -ge $MaxItems)) {
        return
    }

    if ($Value -is [System.Array]) {
        foreach ($item in $Value) {
            Search-ObjectForMessages -Value $item -SourceFile $SourceFile -Tool $Tool -Items $Items -Depth ($Depth + 1) -MaxItems $MaxItems
            if ($Items.Count -ge $MaxItems) {
                break
            }
        }
        return
    }

    if ($Value -isnot [System.Management.Automation.PSCustomObject]) {
        return
    }

    $before = $Items.Count
    Add-TranscriptItemFromObject -Object $Value -SourceFile $SourceFile -Tool $Tool -Items $Items
    if ($Items.Count -gt $before) {
        return
    }

    foreach ($prop in $Value.PSObject.Properties) {
        if ($prop.Name -in @("base_instructions", "instructions", "tools", "tool", "metadata")) {
            continue
        }
        Search-ObjectForMessages -Value $prop.Value -SourceFile $SourceFile -Tool $Tool -Items $Items -Depth ($Depth + 1) -MaxItems $MaxItems
        if ($Items.Count -ge $MaxItems) {
            break
        }
    }
}

function Read-JsonTranscript {
    param(
        [System.IO.FileInfo]$File,
        [string]$Tool,
        [int]$MaxItems
    )

    if ($File.Length -gt 15MB) {
        return @()
    }

    $items = New-Object System.Collections.ArrayList

    try {
        $raw = Get-Content -LiteralPath $File.FullName -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        Search-ObjectForMessages -Value $obj -SourceFile $File.FullName -Tool $Tool -Items $items -Depth 0 -MaxItems $MaxItems
    }
    catch {
        return @()
    }

    return @($items)
}

function Escape-MarkdownCell {
    param([string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    return (($Value -replace "\|", "\|") -replace "\r?\n", " ").Trim()
}

function Format-ByteSize {
    param([int64]$Bytes)

    if ($Bytes -ge 1GB) {
        return "{0:N2} GB" -f ($Bytes / 1GB)
    }
    if ($Bytes -ge 1MB) {
        return "{0:N2} MB" -f ($Bytes / 1MB)
    }
    if ($Bytes -ge 1KB) {
        return "{0:N2} KB" -f ($Bytes / 1KB)
    }
    return "$Bytes B"
}

function Add-MatchedFile {
    param(
        [hashtable]$MatchMap,
        [System.IO.FileInfo]$File,
        [string]$Tool,
        [string]$Root,
        [string]$Reason,
        [string]$MatchedTerm
    )

    if (-not (Test-CopyableFile -File $File)) {
        return
    }

    $key = $File.FullName.ToLowerInvariant()
    if ($MatchMap.ContainsKey($key)) {
        $existing = $MatchMap[$key]
        if ($existing.Tool.IndexOf($Tool, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
            $existing.Tool = "{0}, {1}" -f $existing.Tool, $Tool
        }
        if ($existing.Reason.IndexOf($Reason, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
            $existing.Reason = "{0}; {1}" -f $existing.Reason, $Reason
        }
        return
    }

    $MatchMap[$key] = [pscustomobject]@{
        Tool = $Tool
        Root = $Root
        FullName = $File.FullName
        Name = $File.Name
        Length = $File.Length
        LastWriteTime = $File.LastWriteTime
        Reason = $Reason
        MatchedTerm = $MatchedTerm
        CopiedTo = ""
    }
}

function Scan-WorkspaceStorage {
    param(
        [hashtable]$MatchMap,
        [string]$Tool,
        [string]$Root,
        [string[]]$Terms,
        [int64]$MaxScanBytes
    )

    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        return
    }

    $workspaceDirs = Get-ChildItem -LiteralPath $Root -Directory -Force -ErrorAction SilentlyContinue
    foreach ($dir in $workspaceDirs) {
        $workspaceJsonPath = Join-Path $dir.FullName "workspace.json"
        if (-not (Test-Path -LiteralPath $workspaceJsonPath -PathType Leaf)) {
            continue
        }

        $workspaceJson = Get-Item -LiteralPath $workspaceJsonPath
        $matchedByPath = Find-FirstTerm -Value $workspaceJson.FullName -Terms $Terms
        $matchedByContent = $false

        if ($null -eq $matchedByPath) {
            $matchedByContent = Test-FileContentMatches -File $workspaceJson -Terms $Terms -MaxBytes $MaxScanBytes
        }

        if (($null -eq $matchedByPath) -and (-not $matchedByContent)) {
            continue
        }

        $reason = "workspace.json points to this project"
        $files = Get-ChildItem -LiteralPath $dir.FullName -Recurse -File -Force -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Add-MatchedFile -MatchMap $MatchMap -File $file -Tool $Tool -Root $Root -Reason $reason -MatchedTerm $matchedByPath
        }
    }
}

function Scan-ContentSource {
    param(
        [hashtable]$MatchMap,
        [object]$Source,
        [string[]]$Terms,
        [int64]$MaxScanBytes
    )

    if (-not (Test-Path -LiteralPath $Source.Root -PathType Container)) {
        return
    }

    $files = Get-ChildItem -LiteralPath $Source.Root -Recurse -File -Force -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        if (-not (Test-CopyableFile -File $file)) {
            continue
        }

        if ($Source.ForceInclude) {
            Add-MatchedFile -MatchMap $MatchMap -File $file -Tool $Source.Tool -Root $Source.Root -Reason $Source.Hint -MatchedTerm ""
            continue
        }

        $pathTerm = Find-FirstTerm -Value $file.FullName -Terms $Terms
        if ($null -ne $pathTerm) {
            Add-MatchedFile -MatchMap $MatchMap -File $file -Tool $Source.Tool -Root $Source.Root -Reason "file path matches project" -MatchedTerm $pathTerm
            continue
        }

        if (Test-FileContentMatches -File $file -Terms $Terms -MaxBytes $MaxScanBytes) {
            Add-MatchedFile -MatchMap $MatchMap -File $file -Tool $Source.Tool -Root $Source.Root -Reason "file content mentions project path/name" -MatchedTerm "content"
        }
    }
}

function Copy-EvidenceFiles {
    param(
        [object[]]$Matches,
        [string]$RawRoot
    )

    foreach ($match in $Matches) {
        $toolDir = ConvertTo-SafeName -Value $match.Tool
        $targetDir = Join-Path $RawRoot $toolDir
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

        $hash = Get-StringHashPrefix -Value $match.FullName -Length 10
        $destName = "{0}_{1}" -f $hash, (Split-Path -Leaf $match.FullName)
        $destPath = Join-Path $targetDir $destName
        Copy-Item -LiteralPath $match.FullName -Destination $destPath -Force
        $match.CopiedTo = $destPath
    }
}

function Write-HookEvent {
    param(
        [string]$ProjectFullPath,
        [string]$OutputRoot,
        [string]$ToolName
    )

    New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
    $hookLogPath = Join-Path $OutputRoot "ai-hook-events.jsonl"
    $stdinText = ""

    try {
        if ([Console]::IsInputRedirected) {
            $stdinText = [Console]::In.ReadToEnd()
        }
    }
    catch {
        $stdinText = ""
    }

    $parsedEvent = $null
    $rawEvent = $null
    if (-not [string]::IsNullOrWhiteSpace($stdinText)) {
        try {
            $parsedEvent = $stdinText | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            $rawEvent = $stdinText
        }
    }

    $record = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        tool = $ToolName
        cwd = (Get-Location).Path
        project = $ProjectFullPath
        event = $parsedEvent
        raw = $rawEvent
    }

    ($record | ConvertTo-Json -Depth 40 -Compress) | Add-Content -LiteralPath $hookLogPath -Encoding UTF8

    $readmePath = Join-Path $OutputRoot "README.md"
    if (-not (Test-Path -LiteralPath $readmePath -PathType Leaf)) {
        @(
            "# Live AI Collaboration Log",
            "",
            "This folder is updated automatically by VS Code tasks and/or Claude hooks.",
            "",
            '- `ai-hook-events.jsonl`: raw hook events recorded while the AI assistant uses tools.',
            '- `AI_COLLABORATION_REPORT.md`: generated evidence report when the collector runs.',
            '- `AI_CHAT_HISTORY.md`: generated readable chat extract when the collector runs.',
            '- `raw-logs/`: copied raw assistant session files.'
        ) | Set-Content -LiteralPath $readmePath -Encoding UTF8
    }

    Write-Output '{"status":"logged"}'
}

function Install-ClaudeHook {
    param([string]$ProjectFullPath)

    $settingsDir = Join-Path $ProjectFullPath ".claude"
    $settingsPath = Join-Path $settingsDir "settings.json"
    New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null

    if (Test-Path -LiteralPath $settingsPath -PathType Leaf) {
        $backupPath = "{0}.bak-{1}" -f $settingsPath, (Get-Date -Format "yyyyMMdd-HHmmss")
        Copy-Item -LiteralPath $settingsPath -Destination $backupPath -Force
    }

    $scriptPath = (Join-Path $ProjectFullPath "scripts\collect-ai-collaboration-history.ps1").Replace('\', '/')
    $projectPathForCommand = $ProjectFullPath.Replace('\', '/')
    $command = 'powershell -NoProfile -ExecutionPolicy Bypass -File "{0}" -Hook -Tool claude -ProjectPath "{1}"' -f $scriptPath, $projectPathForCommand

    $settings = [ordered]@{
        hooks = [ordered]@{
            PostToolUse = @(
                [ordered]@{
                    matcher = "*"
                    hooks = @(
                        [ordered]@{
                            type = "command"
                            command = $command
                        }
                    )
                }
            )
            Stop = @(
                [ordered]@{
                    matcher = "*"
                    hooks = @(
                        [ordered]@{
                            type = "command"
                            command = $command
                        }
                    )
                }
            )
        }
    }

    $settings | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $settingsPath -Encoding UTF8
    Write-Host "Claude hook installed: $settingsPath"
}

function Write-Report {
    param(
        [object[]]$MatchedRecords,
        [string]$ProjectFullPath,
        [string]$OutputRoot,
        [string]$ReportPath,
        [string]$ChatPath,
        [string]$ZipPath
    )

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add("# AI Collaboration Evidence Report")
    [void]$lines.Add("")
    [void]$lines.Add("- Project: ``$ProjectFullPath``")
    [void]$lines.Add("- Generated at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')")
    [void]$lines.Add("- Output folder: ``$OutputRoot``")
    if (-not [string]::IsNullOrWhiteSpace($ZipPath)) {
        [void]$lines.Add("- Zip package: ``$ZipPath``")
    }
    [void]$lines.Add("")
    [void]$lines.Add("## Summary")
    [void]$lines.Add("")

    if (@($MatchedRecords).Count -eq 0) {
        [void]$lines.Add("No matching AI history files were found for this project.")
    }
    else {
        $groups = $MatchedRecords | Group-Object Tool | Sort-Object Name
        foreach ($group in $groups) {
            [void]$lines.Add("- $($group.Name): $($group.Count) file(s)")
        }
    }

    [void]$lines.Add("")
    [void]$lines.Add("## Files")
    [void]$lines.Add("")
    [void]$lines.Add("| Tool | Size | Modified | Reason | Original file | Copied file |")
    [void]$lines.Add("| --- | ---: | --- | --- | --- | --- |")

    foreach ($match in ($MatchedRecords | Sort-Object Tool, LastWriteTime, FullName)) {
        $tool = Escape-MarkdownCell -Value $match.Tool
        $size = Format-ByteSize -Bytes $match.Length
        $modified = $match.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        $reason = Escape-MarkdownCell -Value $match.Reason
        $original = Escape-MarkdownCell -Value $match.FullName
        $copied = Escape-MarkdownCell -Value $match.CopiedTo
        [void]$lines.Add("| $tool | $size | $modified | $reason | ``$original`` | ``$copied`` |")
    }

    [void]$lines.Add("")
    [void]$lines.Add("## Submission Notes")
    [void]$lines.Add("")
    [void]$lines.Add("- Submit the zip package or the output folder together with screenshots of the AI CLI/VS Code session.")
    [void]$lines.Add("- Review raw logs before sending. They may contain prompts, terminal output, local file paths, or secrets accidentally pasted during development.")
    [void]$lines.Add('- `AI_CHAT_HISTORY.md` contains a readable extracted timeline. Raw logs are still included for verification.')

    Set-Content -LiteralPath $ReportPath -Value $lines -Encoding UTF8

    $chatLines = New-Object System.Collections.ArrayList
    [void]$chatLines.Add("# AI Chat History Extract")
    [void]$chatLines.Add("")
    [void]$chatLines.Add("Project: ``$ProjectFullPath``")
    [void]$chatLines.Add("")
    [void]$chatLines.Add("This file is generated from matched JSON/JSONL logs. It is a readable extract, not a replacement for raw logs.")
    [void]$chatLines.Add("")

    $totalExtracted = 0
    foreach ($match in ($MatchedRecords | Sort-Object Tool, LastWriteTime, FullName)) {
        $fileInfo = Get-Item -LiteralPath $match.FullName -ErrorAction SilentlyContinue
        if ($null -eq $fileInfo) {
            continue
        }

        $items = @()
        $ext = $fileInfo.Extension.ToLowerInvariant()
        if (($ext -eq ".jsonl") -or ($ext -eq ".log")) {
            $items = @(Read-JsonlTranscript -File $fileInfo -Tool $match.Tool -MaxItems $MaxTranscriptItemsPerFile)
        }
        elseif ($ext -eq ".json") {
            $items = @(Read-JsonTranscript -File $fileInfo -Tool $match.Tool -MaxItems $MaxTranscriptItemsPerFile)
        }

        if (@($items).Count -eq 0) {
            continue
        }

        $totalExtracted += @($items).Count
        [void]$chatLines.Add("## $($match.Tool)")
        [void]$chatLines.Add("")
        [void]$chatLines.Add("Source: ``$($match.FullName)``")
        [void]$chatLines.Add("")

        foreach ($item in $items) {
            $timestamp = $item.Timestamp
            if ([string]::IsNullOrWhiteSpace($timestamp)) {
                $timestamp = "unknown time"
            }
            $text = Limit-Text -Text $item.Text -MaxChars $MaxSnippetChars
            $text = $text.Replace('```', "'''")

            [void]$chatLines.Add("### $($item.Role) - $timestamp")
            [void]$chatLines.Add("")
            [void]$chatLines.Add('```text')
            [void]$chatLines.Add($text)
            [void]$chatLines.Add('```')
            [void]$chatLines.Add("")
        }
    }

    if ($totalExtracted -eq 0) {
        [void]$chatLines.Add('No readable user/assistant messages were extracted. Check raw logs in `raw-logs/`.')
    }

    Set-Content -LiteralPath $ChatPath -Value $chatLines -Encoding UTF8
}

$ProjectFullPath = Resolve-FullPath -Path $ProjectPath
if (-not (Test-Path -LiteralPath $ProjectFullPath -PathType Container)) {
    throw "ProjectPath is not a folder: $ProjectFullPath"
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    if ($Watch -or $Hook) {
        $OutputRoot = Join-Path $ProjectFullPath "ai-collaboration-evidence\live"
    }
    else {
        $OutputRoot = Join-Path $ProjectFullPath ("ai-collaboration-evidence\auto-{0}" -f $stamp)
    }
}
else {
    $OutputRoot = Resolve-FullPath -Path $OutputDir
}

if ($InstallClaudeHook) {
    Install-ClaudeHook -ProjectFullPath $ProjectFullPath
    return
}

if ($Hook) {
    Write-HookEvent -ProjectFullPath $ProjectFullPath -OutputRoot $OutputRoot -ToolName $Tool
    return
}

if ($Watch) {
    Write-Host "Watching AI logs for project: $ProjectFullPath"
    Write-Host "Output folder: $OutputRoot"
    Write-Host "Refresh interval: $WatchIntervalSeconds second(s). Press Ctrl+C to stop."

    while ($true) {
        try {
            $watchArgs = @(
                "-ProjectPath", $ProjectFullPath,
                "-OutputDir", $OutputRoot,
                "-MaxScanFileMB", $MaxScanFileMB,
                "-MaxTranscriptItemsPerFile", $MaxTranscriptItemsPerFile,
                "-MaxSnippetChars", $MaxSnippetChars,
                "-NoZip"
            )

            if ($NoRawCopy) {
                $watchArgs += "-NoRawCopy"
            }

            & $PSCommandPath @watchArgs
        }
        catch {
            Write-Warning "AI log refresh failed: $($_.Exception.Message)"
        }

        Start-Sleep -Seconds $WatchIntervalSeconds
    }
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$RawRoot = Join-Path $OutputRoot "raw-logs"
if (-not $NoRawCopy) {
    New-Item -ItemType Directory -Force -Path $RawRoot | Out-Null
}

$homeDir = $env:USERPROFILE
if ([string]::IsNullOrWhiteSpace($homeDir)) {
    $homeDir = [Environment]::GetFolderPath("UserProfile")
}

$appData = $env:APPDATA
if ([string]::IsNullOrWhiteSpace($appData)) {
    $appData = [Environment]::GetFolderPath("ApplicationData")
}

$localAppData = $env:LOCALAPPDATA
if ([string]::IsNullOrWhiteSpace($localAppData)) {
    $localAppData = [Environment]::GetFolderPath("LocalApplicationData")
}
$terms = Get-ProjectSearchTerms -FullProjectPath $ProjectFullPath
$maxScanBytes = [int64]$MaxScanFileMB * 1MB

$sources = New-Object System.Collections.ArrayList
[void]$sources.Add((New-SearchSource -Tool "Codex CLI" -Root (Join-Path $homeDir ".codex\sessions") -Hint "Codex session logs"))
[void]$sources.Add((New-SearchSource -Tool "Codex CLI" -Root (Join-Path $homeDir ".codex\log") -Hint "Codex local logs"))
[void]$sources.Add((New-SearchSource -Tool "Claude CLI" -Root (Join-Path $homeDir ".claude\projects") -Hint "Claude project logs"))
[void]$sources.Add((New-SearchSource -Tool "Gemini CLI" -Root (Join-Path $homeDir ".gemini") -Hint "Gemini CLI local files"))
[void]$sources.Add((New-SearchSource -Tool "Gemini CLI" -Root (Join-Path $appData "gemini") -Hint "Gemini roaming app data"))
[void]$sources.Add((New-SearchSource -Tool "Gemini CLI" -Root (Join-Path $localAppData "Gemini") -Hint "Gemini local app data"))

$claudeProjectsRoot = Join-Path $homeDir ".claude\projects"
if (Test-Path -LiteralPath $claudeProjectsRoot -PathType Container) {
    $claudeProjectDirs = Get-ChildItem -LiteralPath $claudeProjectsRoot -Directory -Force -ErrorAction SilentlyContinue
    foreach ($dir in $claudeProjectDirs) {
        $term = Find-FirstTerm -Value $dir.Name -Terms $terms
        if ($null -ne $term) {
            [void]$sources.Add((New-SearchSource -Tool "Claude CLI" -Root $dir.FullName -Hint "Claude project directory matches current project" -ForceInclude $true))
        }
    }
}

$editorProfiles = @("Code", "Code - Insiders", "VSCodium", "Cursor", "Windsurf")
foreach ($profile in $editorProfiles) {
    $userRoot = Join-Path $appData ("{0}\User" -f $profile)
    [void]$sources.Add((New-SearchSource -Tool "GitHub Copilot Chat ($profile)" -Root (Join-Path $userRoot "globalStorage\github.copilot-chat") -Hint "Copilot Chat extension storage"))
    [void]$sources.Add((New-SearchSource -Tool "GitHub Copilot ($profile)" -Root (Join-Path $userRoot "globalStorage\github.copilot") -Hint "Copilot extension storage"))
    [void]$sources.Add((New-SearchSource -Tool "Gemini Code Assist ($profile)" -Root (Join-Path $userRoot "globalStorage\google.geminicodeassist") -Hint "Gemini Code Assist extension storage"))
    [void]$sources.Add((New-SearchSource -Tool "Codeium/Windsurf ($profile)" -Root (Join-Path $userRoot "globalStorage\codeium.codeium") -Hint "Codeium extension storage"))
    [void]$sources.Add((New-SearchSource -Tool "Editor Logs ($profile)" -Root (Join-Path $appData ("{0}\logs" -f $profile)) -Hint "Editor logs"))
    [void]$sources.Add((New-SearchSource -Tool "Workspace Storage ($profile)" -Root (Join-Path $userRoot "workspaceStorage") -Hint "Workspace storage" -WorkspaceStorage $true))
}

$matchMap = @{}
foreach ($source in $sources) {
    if ($source.WorkspaceStorage) {
        Scan-WorkspaceStorage -MatchMap $matchMap -Tool $source.Tool -Root $source.Root -Terms $terms -MaxScanBytes $maxScanBytes
    }
    else {
        Scan-ContentSource -MatchMap $matchMap -Source $source -Terms $terms -MaxScanBytes $maxScanBytes
    }
}

$matchedFiles = @($matchMap.Values | Sort-Object Tool, LastWriteTime, FullName)

if (-not $NoRawCopy) {
    Copy-EvidenceFiles -Matches $matchedFiles -RawRoot $RawRoot
}

$reportPath = Join-Path $OutputRoot "AI_COLLABORATION_REPORT.md"
$chatPath = Join-Path $OutputRoot "AI_CHAT_HISTORY.md"
$zipPath = ""
if (-not $NoZip) {
    $zipPath = "$OutputRoot.zip"
}

Write-Report -MatchedRecords $matchedFiles -ProjectFullPath $ProjectFullPath -OutputRoot $OutputRoot -ReportPath $reportPath -ChatPath $chatPath -ZipPath $zipPath

if (-not $NoZip) {
    Compress-Archive -Path $OutputRoot -DestinationPath $zipPath -Force
}

Write-Host "AI history collection complete."
Write-Host "Project: $ProjectFullPath"
Write-Host "Matched files: $($matchedFiles.Count)"
Write-Host "Report: $reportPath"
Write-Host "Chat extract: $chatPath"
if (-not $NoZip) {
    Write-Host "Zip: $zipPath"
}
