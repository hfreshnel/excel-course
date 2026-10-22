param(
	[switch]$SkipTts,
	[switch]$SkipNode,
	[switch]$SkipAvatar
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Step($message) {
	Write-Host "`n== $message" -ForegroundColor Cyan
}

function Run($exe, [string[]]$arguments) {
	& $exe @arguments
	if ($LASTEXITCODE -ne 0) {
		throw "Command failed ($LASTEXITCODE): $exe $($arguments -join ' ')"
	}
}

try {
	Step 'Prerequisites'
	foreach ($tool in 'git', 'py', 'node', 'npm') {
		if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
			throw "Missing prerequisite: $tool"
		}
	}
	if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
		Write-Warning 'ffmpeg not found in PATH. Install it with: winget install Gyan.FFmpeg (then open a new shell).'
	}
	Run 'git' @('lfs', 'install')
	Run 'git' @('lfs', 'pull')

	Step 'Automation environment (.venv)'
	if (-not (Test-Path '.venv\Scripts\python.exe')) {
		Run 'py' @('-3.14', '-m', 'venv', '.venv')
	}
	Run '.venv\Scripts\python.exe' @('-m', 'pip', 'install', '-r', 'requirements.txt')

	if (-not $SkipNode) {
		Step 'Compositing (Remotion)'
		Push-Location compositing
		try {
			Run 'npm' @('ci')
			Run 'npm' @('run', 'typecheck')
		} finally {
			Pop-Location
		}
	}

	if (-not $SkipTts) {
		Step 'Voice synthesis environment (.venv-tts, about 5 GB)'
		$cuda = 'https://download.pytorch.org/whl/cu128'
		if (-not (Test-Path '.venv-tts\Scripts\python.exe')) {
			Run 'py' @('-3.14', '-m', 'venv', '.venv-tts')
		}
		$ttsPython = '.venv-tts\Scripts\python.exe'
		Run $ttsPython @('-m', 'pip', 'install', 'torch==2.11.0', 'torchaudio==2.11.0', '--index-url', $cuda)
		Run $ttsPython @('-m', 'pip', 'install', '--no-deps', 'chatterbox-tts==0.1.7')
		Run $ttsPython @('-m', 'pip', 'install', '-r', 'requirements-tts.txt', '--extra-index-url', $cuda)
	}

	if (-not $SkipAvatar) {
		Step 'Normalized avatar poses'
		Run '.venv\Scripts\python.exe' @('tools\normalize_avatar.py')
	}

	Write-Host "`nDone. Models (Chatterbox, Whisper, Demucs) are downloaded on first use (about 7 GB in %USERPROFILE%\.cache\huggingface)." -ForegroundColor Green
	Write-Host 'Not in git, to restore from your own backup: assets\voice\ (cloning reference), exercises\*\states\, video-XX\recordings\ and renders\.'
} catch {
	Write-Host "Setup failed: $_" -ForegroundColor Red
	exit 1
}
