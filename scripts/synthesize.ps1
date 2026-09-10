# Synthesizes the gate/demo corpus audio using Windows SAPI voices, at exactly
# 16kHz/16-bit/mono so no resampling step is needed downstream.
# See scripts/build_synth_jobs.py for what gets synthesized and why.

Add-Type -AssemblyName System.Speech

$jobs = Get-Content "gate/synth_jobs.json" -Raw | ConvertFrom-Json
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
    16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
    [System.Speech.AudioFormat.AudioChannel]::Mono)

New-Item -ItemType Directory -Force -Path "corpus/audio/_raw" | Out-Null

foreach ($job in $jobs) {
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $voice = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -like "*$($job.voice)*" }
    if ($voice) { $synth.SelectVoice($voice[0].VoiceInfo.Name) }
    $synth.Rate = $job.rate
    $outPath = "corpus/audio/_raw/$($job.out).wav"
    $synth.SetOutputToWaveFile($outPath, $fmt)
    $synth.Speak($job.text)
    $synth.Dispose()
    Write-Host "synthesized $outPath <- '$($job.text)' ($($job.voice), rate=$($job.rate))"
}

Write-Host "done: $($jobs.Count) clips"
