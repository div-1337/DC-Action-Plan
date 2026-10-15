# Project Directive: DataCatalyst — Automated Tech + Operations Engine

## 1. Context & Strategic Vision
DataCatalyst bridges the critical gap between raw speech datasets and production-grade Voice AI reliability. Rather than operating purely as a manual data labeling vendor or purely as a theoretical benchmark tool, DataCatalyst delivers a **dual-engine hybrid offering**:

1. **Automated Tech Engine:** Programmatic, async adversarial stress-testing harnesses, VAD audio slicing, acoustic corruption pipelines, and continuous Voice AI benchmarking.
2. **Specialized Operations Engine:** High-fidelity human-in-the-loop conversational data collection, dual ground-truth transcription, live human red-team calling, and domain-specific Hinglish entity tagging.

This unified approach allows Voice AI builders (targeting OpenAI Realtime, Deepgram Nova/Flux, Sarvam, ElevenLabs, Cartesia, etc.) to rigorously evaluate, red-team, and harden their models against real-world Indian conversational chaos.

---

## 2. Service Offerings Portfolio

### Track A: Automated Tech Services (Software & Automation Engine)

1. **Automated Voice AI Adversarial Testing & Benchmarking Harness**
   * **Turn-Taking & Premature Cutoff Testing:** Detects if an API triggers `speech_stopped` or cuts off speakers during natural mid-thought hesitations (100ms–800ms pauses).
   * **Phantom Noise & Breathing Hallucination Testing:** Programmatically feeds silence, microphone pops, heavy breathing, and ambient cafe/traffic noise to identify spurious token generation or unsolicited bot interruptions.
   * **Bilingual / Hinglish Entity & Numeral Corruption Tests:** Evaluates model retention on mixed alphanumeric tokens, Hindi/English numerals, names, and currency amounts across code-switched dialogues.
   * **Latency & RTT Profiling:** High-resolution measurement of Time-to-First-Token (TTFT), Voice-to-Voice end-of-turn latency, and WebSocket connection stability.

2. **Automated Audio Slicing & Boundary Extraction Pipeline**
   * Silero VAD-based automated segmentation of raw 20+ minute dual-channel/multitrack audio into targeted test units (e.g., 3s–8s windows ending at critical pause boundaries).
   * Automatic categorization of clips into: *clean turns*, *hesitation turns*, *overlapping speech*, and *background noise intervals*.

3. **Acoustic Stress & Telephony Degradation Injection**
   * Automated synthetic acoustic corruption: VoIP packet jitter, 8kHz telephony downsampling, ambient noise overlay, and dynamic microphone clipping to benchmark robustness under poor network conditions.

4. **Continuous Voice CI/CD Regression Harness**
   * Headless test suite integration: Run automated regression tests against staging Voice AI endpoints on every prompt, model, or provider update.
   * Auto-exports failing audio clips and structured diagnostic JSONs to an isolated triage directory (`failures/`).

---

### Track B: Operations & Human-in-the-Loop Services (Data & Red-Teaming Ops)

1. **Proprietary & Custom Conversational Audio Sourcing**
   * Spontaneous, multi-speaker, dual-channel conversational sessions (Hindi, Hinglish, and regional Indian dialects).
   * Real telephony (VoIP, WebRTC, cellular) and dynamic acoustic environments with documented, legally binding contributor consent and automated PII scrubbing.

2. **Dual Ground-Truth Transcription & Diarization Ops**
   * **The 1-Step Human Verbatim Base Layer:** Transcribers capture raw acoustic reality—preserving every filler word, false start, stutter, and breathing sound with standardized tags (`[filler:haan]`, `[pause]`, `[laughter]`).
   * **Automated AI/Rule Normalizer (`normalize_transcript.py`):** Programmatically derives the second clean `normalized` ground-truth layer by stripping fillers, collapsing stutters, formatting numeric digits, and applying standard Hindi punctuation.
   * **Efficiency Impact:** Eliminates double-entry transcription, slashes human turnaround from 30 days to 5 days, and guarantees 100% human ground truth for turn-taking benchmarks alongside clean text for ASR WER evaluation.
   * Millisecond-accurate human-verified speaker diarization and turn timestamping.

3. **Live Human Red-Teaming & "In-The-Wild" Adversarial Calling**
   * Human red-team callers challenging live voicebots with realistic conversational stress: rapid interruptions, abrupt topic shifts, emotional variance, colloquial slang, and heavy background chaos.
   * Guardrail testing: Prompt injection, social engineering, and out-of-domain conversational traps.

4. **Subjective Quality (MOS) & Conversational Flow Scoring**
   * Human evaluation of naturalness, conversational latency perception, voice prosody, accent authenticity, and response appropriateness across regional user demographics.

5. **Domain-Specific NLU, Slot Tagging & Entity Annotation**
   * Specialized intent labeling and entity extraction for high-stakes verticals (BFSI, Healthcare, Logistics, E-commerce, Customer Support).

---

## 3. Technical Stack
* **Core Language:** Python 3.10+
* **Concurrency & Networking:** `asyncio`, `httpx`, `websockets` (for parallel real-time streaming against voice endpoints)
* **Audio Processing:** `torchaudio`, `librosa`, `soundfile`, `silero-vad`
* **Local Hardware Execution:** AMD Ryzen 7 5700X3D, 16GB RAM, NVIDIA RTX 3060 12GB (capable of local transcription with Whisper/Faster-Whisper and local embedding/judge verification)

---

## 4. Software Architecture & Implementation Plan

```
datacatalyst-engine/
│
├── audio_pipeline/
│   ├── extract_turns.py       # Silero VAD audio slicer & turn boundary cataloguer
│   ├── stress_injector.py     # Acoustic degradation & noise overlay generator
│   └── dataset_loader.py      # Dual-channel / multitrack session loader
│
├── benchmark_harness/
│   ├── connectors/            # Provider streaming connectors
│   │   ├── base.py            # Abstract streaming base class
│   │   ├── openai_realtime.py # OpenAI Realtime WebSocket client
│   │   ├── deepgram.py        # Deepgram Live ASR client
│   │   ├── sarvam.py          # Sarvam AI speech API client
│   │   └── elevenlabs.py      # ElevenLabs Conversational / TTS client
│   ├── evaluators/
│   │   ├── cutoff.py          # Premature cutoff & hesitation tester
│   │   ├── hallucination.py   # Phantom speech / noise hallucination tester
│   │   └── entity_accuracy.py # Hinglish numerals & entity accuracy comparator
│   └── benchmark_runner.py    # Main async parallel test orchestrator
│
├── reports/
│   ├── failures/              # Isolated triage clips + failure JSON metadata
│   └── summary_generator.py   # Aggregated benchmark metrics (P50/P90, WER, cutoff rates)
│
└── config/
    └── benchmark_config.yaml  # API keys, endpoint URLs, thresholds, and clip sets
```

---

## 5. Phased Roadmap

* **Phase 1 (Tech Core):** Build `extract_turns.py` (VAD slicer) and the foundational async `benchmark_runner.py` with the first provider connector.
* **Phase 2 (Adversarial Suites):** Implement the cutoff, hallucination, and Hinglish entity evaluator modules.
* **Phase 3 (Acoustic Stress Engine):** Implement `stress_injector.py` to test degradation under packet loss, low bitrate, and ambient background noise.
* **Phase 4 (Ops Integration):** Wire automated test failure outputs into a structured format suitable for human red-team and annotation handoff.
