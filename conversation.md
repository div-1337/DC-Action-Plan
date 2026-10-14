# DataCatalyst: Strategic & Technical Conversation Log

---

## 1. Context & Overview
* **Project:** DataCatalyst ([datacatalyst.in](https://datacatalyst.in))
* **Founder:** Divyam Bhatia (Sri Ganganagar, Rajasthan, India)
* **Objective:** Expand DataCatalyst from raw speech dataset collection into a high-value **Dual-Engine Platform** combining:
  1. **Automated Tech & Systems Engineering:** VAD audio slicing, async API benchmarking, adversarial failure testing (cutoffs, noise hallucinations, Hinglish entity corruption), and acoustic stress injection.
  2. **Specialized Operations & Human Data Engine:** High-fidelity conversational Hindi datasets, dual-ground truth transcription, speaker diarization, and live human red-team testing.

---

## 2. Current Asset Audit: 15 Hours Hindi Conversational Audio

| Metric | Status | Evaluation & Implications |
| :--- | :--- | :--- |
| **Total Volume** | 15 Hours | Ideal for an **Enterprise Evaluation, Fine-Tuning, and Red-Teaming Benchmark** (not foundation pre-training). |
| **Speaker Count** | 10 to ~15 unique speakers | **Strong.** ~1 hour per speaker provides solid acoustic diversity for an evaluation benchmark. |
| **Channel Format** | Dual-channel (Speaker separated) | **Gold Standard.** Clean channel separation enables automated, 100% accurate ground-truth diarization and overlap benchmarking. |
| **Transcription Status** | Untranscribed | Moving to **AI-Assisted Human-in-the-Loop (HITL)** to reduce timeline from 1 month to 4–6 days. |
| **Legal Consent** | 100% Explicitly Consented | **Audit-Ready.** Complies with India's DPDP Act 2023 and EU AI Act requirements. |
| **Standardization Rules** | To be authored by founder | Critical for defining Devanagari vs. Latin spelling, numeral formats, and disfluency tags. |

---

## 3. High-Value Packaging Breakdown (A through E)

### A. Triple-Layer Transcriptions
* **Decision:** Accepted (Doable, will be executed).
* **Format:**
  1. *Verbatim Devanagari:* Preserving disfluencies (*हाँ, अच्छा, मतलब, अरे*), false starts, stutters, and thinking pauses.
  2. *Normalized Clean Devanagari:* Standardized for standard ASR WER/CER evaluation.
  3. *Romanized / Hinglish (Latin Script):* Essential for enterprise LLMs and Voicebots operating in English-script Hinglish.

### B. Curated Adversarial Benchmark Slices
* **Decision:** Accepted ("Will do").
* **Deliverables:**
  * **Mid-Thought Pause Slice:** Evaluates premature cutoff triggers on 100ms–800ms hesitations.
  * **Hinglish Entity & Numeral Slice:** Evaluates model retention on phone numbers, currency (Lakhs/Crores), and alphanumeric IDs.
  * **Overlapping Speech Slice:** Evaluates cross-talk handling.
  * **Ambient Noise Slice:** Real-world VoIP background acoustics.

### C. Diarization Testing via Dual/Multi-Channel Merging (Voclara.com Infrastructure)
* **Architecture:** 5 speakers connect remotely via the founder's proprietary platform **voclara.com**.
* **Zero Acoustic Bleed:** Because each speaker connects from their own browser/device in separate environments, there is **zero microphone bleed / acoustic crosstalk**.
* **Automatic Ground Truth:** Each speaker has an isolated track (`speaker_1.wav` ... `speaker_5.wav`). Transcribing each track independently produces 100% accurate speaker attribution with zero diarization guesswork.
* **Overlapping Speech Math:** Since all tracks are synchronized on `voclara.com`, cross-talk intervals are calculated purely by mathematical timestamp comparison.
* **Volume Benchmark:** 2 to 3 hours of a 5-speaker conversation generates **10 to 15 track-hours** of pristine, multi-party conversational Hindi audio. This is more than sufficient for an enterprise meeting/conversational AI evaluation benchmark.

### D. Acoustic Profiling & Metrics (SNR, Clipping, Frequency)
* **User Question:** Can we use a website or tool to extract acoustic metrics?
* **Solution & Strategy:**
  * **Why Avoid Third-Party Websites:** Uploading proprietary, unreleased enterprise audio to commercial websites poses IP leakage, privacy, and confidentiality risks.
  * **Recommended Approach:** A lightweight local Python script (using `librosa`, `scipy`, `soundfile`, `wada-snr`) executed on the local workstation (RTX 3060).
  * **Metrics Generated Automatically (in ~30 seconds for 15 hours):**
    1. *Signal-to-Noise Ratio (SNR in dB)*
    2. *Digital Clipping Rate (% of samples hitting 0 dBFS)*
    3. *Dynamic Range & RMS Energy*
    4. *Spectral Bandwidth & Frequency Rolloff (verifying 48kHz / 16kHz preservation)*
  * **Alternative GUI Tool:** *Audacity* (free, open-source, local) or *Sonic Visualiser* for visual frequency and waveform inspection.

### E. Commercial Baseline Benchmark Report
* **Decision:** To be configured after transcription draft is ready.
* **Strategy:** Run the 15 hours through Whisper (large-v3), Sarvam Saaras, Deepgram Nova-2, and Google Chirp. Publish a comparative reliability scorecard to generate enterprise inbound interest.

---

## 4. Multi-Speaker Recording Strategy & Acoustic Protocol (Voclara.com)

### A. The Core Principle: "Acoustically CLEAN, Conversationally MESSY"
* **Record Acoustically Clean:**
  * **Additive Noise is Solvable:** Taking pristine clean audio and synthetically injecting calibrated noise (office chatter, traffic, ceiling fan hum, 8kHz telephony bandpass) via Python (`stress_injector.py`) is 100% controllable.
  * **Irreversible Distortion:** Audio recorded with loud background television or rattling fans cannot be cleaned up without introducing severe phase distortion and spectral subtraction artifacts.
* **Record Conversationally Messy:**
  * Avoid scripted, news-anchor speech.
  * Encourage spontaneous debates (IPL, startups, street food, politics) with natural interruptions (*"Arre suno toh meri baat..."*), stutters, laughter, and fillers (*"umm", "matlab", "achha"*).

### B. The "3-for-1" Dataset Multiplier
By recording pristine multi-track masters on `voclara.com`, a single 3-hour recording session can be exported into three distinct commercial benchmark tiers:
1. **Tier 1 (Clean Master Benchmark):** Pristine VoIP meeting benchmark for baseline transcription & diarization.
2. **Tier 2 (Office / Cafeteria Stress Benchmark):** Clean audio + synthetically added office chatter at calibrated SNR (+10 dB).
3. **Tier 3 (Telephony / Street Stress Benchmark):** Clean audio + 8kHz G.711 downsampling + traffic noise (+5 dB).

### C. Voclara.com Client-Side Audio Settings (`getUserMedia`)
To prevent browser DSP from crushing natural speech subtleties, configure WebRTC audio constraints:
```javascript
const audioConstraints = {
  echoCancellation: true,  // Prevents speaker feedback loop
  noiseSuppression: false, // Preserves quiet fillers, breathing, and natural pauses
  autoGainControl: false,   // Prevents volume pumping artifacts
  channelCount: 1,
  sampleRate: 48000
};
```

### D. Speaker Onboarding Checklist for Voclara Sessions
1. **Quiet Environment:** Closed doors, loud ceiling fans / TV switched off.
2. **Microphone Setup:** Directional headset or wired earphone mic positioned close to the mouth (avoiding distant laptop built-in mics).
3. **Conversational Dynamic:** Natural, rapid, colloquial Hindi banter with uninhibited cross-talk.

---

## 5. Immediate Action Items

1. **Standardization Document:** Create the 1-page "DataCatalyst Hindi Annotation Guideline" (handling Devanagari vs. English loan words, numeral formats, and disfluency tags).
2. **AI-Assisted HITL Pipeline:** Run local Whisper / Sarvam on the RTX 3060 to generate first-pass draft transcripts for the 15 hours.
3. **Local Acoustic Extractor Script:** Run a batch Python script to extract SNR, clipping, and RMS metrics for all 15 hours.
4. **Channel Merge & Diarization Script:** Merge dual-channel files into single-channel test inputs for automated DER evaluation.
5. **Voclara Session Setup:** Test 5-speaker multi-track recording with `noiseSuppression: false` and synchronized global start timestamps.

