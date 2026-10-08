param(
	[Parameter(Mandatory = $true)][string]$InputPath,
	[Parameter(Mandatory = $true)][string]$OutputDir,
	[string]$VoiceCulture = "fr-FR",
	[int]$Rate = 1
)

# Synthesizes each chunk of $InputPath (JSON array of strings) to chunk-NNNN.wav and writes words.json:
# one entry per chunk with the words and their audio offsets (seconds), from SpeakProgress events.
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
	$voice = $synthesizer.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -eq $VoiceCulture } | Select-Object -First 1
	if ($null -ne $voice) {
		$synthesizer.SelectVoice($voice.VoiceInfo.Name)
	} else {
		Write-Warning "No $VoiceCulture voice found, using $($synthesizer.Voice.Name)"
	}
	$synthesizer.Rate = $Rate
	# AudioPosition is always computed at the voice native rate (16 kHz for the Desktop voices): any other output rate skews word offsets
	$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
	$chunks = Get-Content -Raw -Encoding UTF8 -LiteralPath $InputPath | ConvertFrom-Json
	# Without -Action, events are only queued: reading them after each Speak keeps them in order and complete
	$null = Register-ObjectEvent -InputObject $synthesizer -EventName SpeakProgress -SourceIdentifier "sapiProgress"
	$results = New-Object System.Collections.ArrayList
	$index = 0
	foreach ($chunk in $chunks) {
		$wavePath = Join-Path $OutputDir ("chunk-{0:D4}.wav" -f $index)
		$synthesizer.SetOutputToWaveFile($wavePath, $format)
		$synthesizer.Speak([string]$chunk)
		$synthesizer.SetOutputToNull()
		$words = New-Object System.Collections.ArrayList
		foreach ($progress in @(Get-Event -SourceIdentifier "sapiProgress" -ErrorAction SilentlyContinue)) {
			$progressArgs = $progress.SourceEventArgs
			$null = $words.Add([ordered]@{ text = $progressArgs.Text; start = $progressArgs.AudioPosition.TotalSeconds; position = $progressArgs.CharacterPosition })
			Remove-Event -EventIdentifier $progress.EventIdentifier
		}
		$null = $results.Add([ordered]@{ wave = (Split-Path $wavePath -Leaf); words = @($words) })
		$index++
	}
	Unregister-Event -SourceIdentifier "sapiProgress"
	$json = ConvertTo-Json -InputObject @($results) -Depth 6
	[System.IO.File]::WriteAllText((Join-Path $OutputDir "words.json"), $json, (New-Object System.Text.UTF8Encoding($false)))
	Write-Output "voice=$($synthesizer.Voice.Name) chunks=$index"
} finally {
	$synthesizer.Dispose()
}
