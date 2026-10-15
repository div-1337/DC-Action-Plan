# DataCatalyst: 3-Day Technical & Commercial Sprint Plan
## Unlocking Immediate Value from the 15-Hour Hindi Audio Asset (Zero-Transcription Dependency)

---

## 1. Executive Context & Objective

* **Current Available Asset:** 15 hours of dual-channel, speaker-separated conversational Hindi audio (~15 speakers, fully consented).
* **Constraints & Ground Rules:**
  1. **Zero dependency on human transcription** (avoids the 1-month transcription bottleneck).
  2. **Zero dependency on new recordings** (does not wait for the 5-speaker Voclara session).
  3. **High-impact execution:** Deliver an automated acoustic audit, an indexed audio testbed, a working adversarial test harness (detecting premature cutoffs and phantom noise hallucinations), a synthetic stress engine, and a client-facing dataset specification sheet in **72 hours**.

---

## 2. 72-Hour Sprint Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               72-HOUR SPRINT MAP                                 │
├─────────────────────────┬──────────────────────────┬─────────────────────────────┤
│          DAY 1          │          DAY 2           │            DAY 3            │
│  Acoustic Audit, Bleed  │  "Zero-Text" Adversarial │  Synthetic Stress Engine &  │
│    Audit & VAD Slicing  │       Test Harness       │  Enterprise Spec Packaging  │
├─────────────────────────┼──────────────────────────┼─────────────────────────────┤
│ • File standardisation  │ • Noise hallucination    │ • Telephony downsampling    │
│ • SNR, clipping & bleed │   test runner            │ • Synthetic noise overlays  │
│ • Silero VAD turn/pause │ • Premature cutoff test  │ • Faster-Whisper draft test │
│   cataloguing           │ • Failure triage logger  │ • Enterprise spec sheet     │
└─────────────────────────┴──────────────────────────┴─────────────────────────────┘
```

---

## 3. DAY 1: Audio Inventory, Acoustic Health Certification & VAD Indexing

### Goal
Transform an unorganized folder of raw audio files into a certified, quality-audited, and timestamp-indexed audio repository.

### Task 1.1: Audio File Standardization & Inventory Scanner
* **Script:** `scripts/inventory_audit.py`
* **Actions:**
  * Scan all audio files across the 15-hour collection.
  * Verify audio parameters: Sample rate (48,000 Hz target), Bit depth (16-bit PCM), Channel count (Stereo / 2-channel mono split).
  * Standardize naming convention: `DC_HI_S<session_id>_spk<A>_spk<B>.wav`.
  * Output: `manifests/raw_inventory.json`.

### Task 1.2: Acoustic Quality & Channel Bleed Profiler
* **Script:** `scripts/acoustic_audit.py`
* **Actions (Local execution on RTX 3060):**
  * Calculate **Signal-to-Noise Ratio (SNR in dB)** across each speaker track.
  * Detect **Digital Clipping Rate** (percentage of samples at 0 dBFS).
  * Compute **Channel Bleed Score:** Measure RMS energy on Channel 1 during verified active speech frames on Channel 0 (confirming zero/negligible acoustic crosstalk).
  * Output: `reports/acoustic_health_report.json` with per-file pass/warn/fail grades.

### Task 1.3: Silero VAD Slicing & Boundary Cataloging
* **Script:** `audio_pipeline/extract_turns.py`
* **Actions:**
  * Run **Silero VAD v5** locally on GPU (`cuda`) across all 15 hours.
  * Automatically segment and index:
    1. **Active Speech Turns:** Turn start and end timestamps per speaker.
    2. **Thinking Pauses / Hesitations:** Intra-speaker silent gaps between **200ms and 800ms** where the same speaker paused before continuing.
    3. **Ambient Room Silence & Noise:** Non-speech segments (>1.0s) containing only background room tone, breathing, or fan noise.
    4. **Overlapping Speech:** Simultaneous active speech timestamps on both Channel 0 and Channel 1.
* **Output:**
  * `manifests/turn_index.json`
  * Slice directories:
    * `test_clips/ambient_silence/` (50+ isolated room tone/breathing clips)
    * `test_clips/hesitations/` (100+ isolated thinking pause clips)
    * `test_clips/overlaps/` (All cross-talk segments)

### Day 1 Acceptance Criteria
- [ ] 100% of the 15 hours cataloged in `raw_inventory.json`.
- [ ] Certified SNR, clipping, and bleed scores in `acoustic_health_report.json`.
- [ ] VAD slicing complete with extracted `ambient_silence/` and `hesitations/` clip folders.

---

## 4. DAY 2: "Zero-Text" Adversarial Test Harness (Cutoffs & Phantom Hallucinations)

### Goal
Build the automated testing runner to stream Day 1 clips into commercial speech APIs and programmatically detect failures without needing transcriptions.

### Task 2.1: The Phantom Noise & Breathing Hallucination Test
* **Script:** `benchmark_harness/hallucination_test.py`
* **Target APIs:** OpenAI Realtime API (WebSocket), Deepgram Live ASR, Sarvam AI.
* **Mechanism:**
  * Asynchronously stream audio clips from `test_clips/ambient_silence/` (pure background room tone, microphone rustle, and caller breathing).
  * **Evaluation Logic:**
    * If the API emits *any* text tokens or triggers a conversational response: **FAIL (Phantom Hallucination)**.
    * If the API remains silent / returns empty transcript: **PASS**.
  * Record round-trip response time and token count.

### Task 2.2: The Premature Cutoff & Pause-Tolerance Test
* **Script:** `benchmark_harness/cutoff_test.py`
* **Mechanism:**
  * Stream audio clips from `test_clips/hesitations/` where a speaker has a known mid-thought pause (e.g., 300ms, 500ms, 800ms).
  * **Evaluation Logic:**
    * Flag if the target API fires an early `speech_stopped` event or starts generating an assistant response *before* the speaker finishes their turn.
    * Quantify the **Cutoff Threshold** for each commercial API (e.g., *"Sarvam cuts off at 350ms pause; OpenAI Realtime cuts off at 500ms pause"*).

### Task 2.3: Automated Failure Logger & Triage Exporter
* **Script:** `benchmark_harness/failure_logger.py`
* **Mechanism:**
  * For every test failure, automatically copy the audio clip to `reports/failures/<error_type>/`.
  * Emit a structured diagnostic JSON file containing:
    ```json
    {
      "test_id": "HAL_042",
      "error_type": "phantom_hallucination",
      "provider": "openai_realtime",
      "audio_file": "DC_HI_S03_ambient_07.wav",
      "audio_duration_ms": 3200,
      "returned_text": "हाँ बोलिए",
      "timestamp": "2026-10-14T18:30:00Z"
    }
    ```

### Day 2 Acceptance Criteria
- [ ] `benchmark_runner.py` successfully connects and streams audio chunks via async WebSockets/HTTP.
- [ ] Noise hallucination test executed across at least two providers (e.g., OpenAI, Deepgram, or Sarvam).
- [ ] Structured failure reports and audio clips automatically logged to `reports/failures/`.

---

## 5. DAY 3: Synthetic Stress Engine & Enterprise Spec Packaging

### Goal
Build the acoustic degradation pipeline and produce an authoritative enterprise dataset specification sheet ready for prospective clients and partners.

### Task 3.1: Synthetic Acoustic Degradation Engine
* **Script:** `audio_pipeline/stress_injector.py`
* **Transformations (Applied programmatically to clean test clips):**
  1. **Telephony Downsampling:** Convert 48kHz studio audio to 8,000 Hz 8-bit $\mu$-law / G.711 codec emulation (simulating standard Indian cellular telephony).
  2. **Calibrated Noise Overlay:** Mix synthetic Indian ambient noise (street traffic, ceiling fan hum, busy office) at controlled SNR levels (+15 dB, +10 dB, +5 dB).
  3. **VoIP Packet Loss Emulation:** Inject random 30ms–80ms audio dropouts/jitter to stress-test real-time streaming robustness.
* **Output:** `test_clips/stressed/` containing telephony, noisy, and degraded test variants.

### Task 3.2: Automated Transcript Normalizer & Filler Stripper
* **Script:** `scripts/normalize_transcript.py`
* **Architectural Strategy (Human-in-the-Loop Optimization):**
  * **The 1-Step Human Protocol:** Transcribers perform only **ONE** task: typing raw verbatim speech with simple acoustic tags (`[pause]`, `[filler:haan]`, `[filler:matlab]`, `[laughter]`). They do not waste time creating a second clean version by hand.
  * **Automated Dual-Layer Generation:**
    1. Input: Human-transcribed `verbatim` text.
    2. Processing: Script uses rule-based regex and local/LLM normalization to programmatically strip thinking fillers, collapse false-start stutters (*"मैं... मैं"* $\rightarrow$ *"मैं"*), format numerals (*"पांच सौ"* $\rightarrow$ `500`), and apply standard Hindi punctuation (`।`, `?`, `,`).
    3. Output: Automatically generates the clean `normalized` ground-truth layer.
  * **Impact:** Cuts human transcription labor by **50%**, reduces delivery timeline from **30 days to 5 days**, and guarantees 100% human ground-truth provenance.

### Task 3.3: Enterprise Dataset Specification & Benchmark Card
* **Deliverable:** `DATASET_SPEC_15H.md` (and optional PDF export).
* **Contents:**
  1. **Corpus Overview:** 15 Hours, 15 Distinct Speakers, Dual-Channel 48kHz PCM Mono.
  2. **Acoustic Certification:** Verified average SNR (>28 dB), 0% digital clipping, < -45 dB cross-channel bleed.
  3. **Adversarial Benchmark Inventory:** Count of cataloged hesitation clips, silence/noise clips, and cross-talk overlaps.
  4. **Compliance & Legal Guarantee:** Explicit contributor consent statement under India's DPDP Act 2023.
  5. **Licensing Tiers:** Non-exclusive enterprise evaluation license vs. full exclusive ownership.

### Day 3 Acceptance Criteria
- [ ] `stress_injector.py` working and producing calibrated noisy/telephony audio clips.
- [ ] Complete test harness pipeline functional (`extract_turns.py` $\rightarrow$ `stress_injector.py` $\rightarrow$ `benchmark_runner.py`).
- [ ] Polished, enterprise-grade `DATASET_SPEC_15H.md` published and ready for client distribution.

---

## 6. Execution Command Reference & Stack

* **Environment:** Python 3.10+, PyTorch with CUDA 12.x, `torchaudio`, `librosa`, `soundfile`, `websockets`, `httpx`.
* **Hardware Context:** AMD Ryzen 7 5700X3D (8C/16T), 16GB RAM, NVIDIA GeForce RTX 3060 12GB.

| Day | Primary Script | Command Example | Key Output |
| :--- | :--- | :--- | :--- |
| **Day 1** | `extract_turns.py` | `python audio_pipeline/extract_turns.py --input-dir ./raw_audio --output-dir ./test_clips` | `manifests/turn_index.json` |
| **Day 2** | `benchmark_runner.py` | `python benchmark_harness/benchmark_runner.py --test hallucination --provider openai` | `reports/failures/` |
| **Day 3** | `stress_injector.py` | `python audio_pipeline/stress_injector.py --input ./test_clips --snr 10 --telephony` | `test_clips/stressed/` |
