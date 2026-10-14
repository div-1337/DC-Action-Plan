# DataCatalyst: Comprehensive Project & Architecture Overview

---

## 1. Executive Summary & Core Mission

**DataCatalyst** ([datacatalyst.in](https://datacatalyst.in)) is an enterprise-focused Voice AI reliability and speech data company founded by **Divyam Bhatia**, headquartered in Sri Ganganagar, Rajasthan, India.

The company was founded to solve a critical bottleneck in the global AI ecosystem: **the unreliability of Voice AI models in complex, multilingual, and noisy real-world conversational environments—specifically across Indian languages and accents.** 

While the broader AI industry has historically treated speech data as a commodity (often relying on scraped, unconsented YouTube audio, low-fidelity synthetic data, or noisy crowd-sourced recordings), DataCatalyst operates on a **dual-engine model**:
1. **The Specialized Operations Engine:** High-fidelity, ethically sourced, multi-speaker conversational audio collection, dual-layer ground truth transcription, millisecond-accurate diarization, and live human red-team testing.
2. **The Automated Systems Engineering & Adversarial Tech Engine:** Programmatic, async stress-testing harnesses, VAD-driven pause and boundary extraction, acoustic corruption pipelines, and continuous automated benchmarking across commercial Speech-to-Speech and Voice AI APIs.

By marrying high-touch human data operations with automated systems engineering, DataCatalyst enables AI laboratories, enterprise voicebot developers, and foundation model teams to both **train** models on gold-standard data and **harden** production voice agents against catastrophic conversational failures.

---

## 2. Market Problem & Industry Context

### 2.1 The Indian Voice AI Gap
India is one of the most voice-first digital economies in the world, with over a billion potential voice users across 22 official languages and hundreds of dialects. However, state-of-the-art commercial Voice AI models consistently struggle in the Indian context due to three structural factors:
* **Code-Switching & Hinglish:** Natural Indian speech fluidly alternates between Hindi, English, and regional vernaculars within single sentences (e.g., *"Maine payment confirm kar diya hai, please receipt send kar do"*). Models frequently corrupt entity names, currency amounts, and technical terms across language boundaries.
* **Conversational Dynamics & Disfluencies:** Spontaneous Indian speech is filled with conversational fillers (*umm*, *haan*, *matlab*, *achha*), mid-sentence false starts, and variable thinking pauses. Standard models misinterpret thinking pauses as turn completions, resulting in premature interruptions.
* **Acoustic Reality:** The vast majority of production voice interactions occur over VoIP, WebRTC, or cellular telephony (often in high-noise ambient settings like streets, public transport, or open offices), rather than pristine studio conditions.

### 2.2 The Legal & Compliance Crisis
With the enforcement of the **EU AI Act** and **India’s Digital Personal Data Protection (DPDP) Act**, enterprise AI teams face severe legal, financial, and reputational liabilities if their training or fine-tuning pipelines ingest unconsented, scraped, or PII-laden data. Provenance, auditability, and explicit commercial AI training consent are now mandatory enterprise prerequisites.

### 2.3 The Voice Agent Reliability Deficit
Real-time conversational Voice AI APIs (OpenAI Realtime API, Deepgram Nova/Flux, Sarvam AI, ElevenLabs, Cartesia) are rapidly replacing legacy STT $\rightarrow$ LLM $\rightarrow$ TTS stacked architectures. However, these real-time systems suffer from severe edge-case bugs:
* **Premature Cutoffs:** The bot interrupts users while they are gathering their thoughts.
* **Phantom Noise Hallucinations:** Ambient room noise, microphone clicks, or caller breathing trigger spurious responses.
* **Latency Spikes:** Jitter and latency spikes break conversational turn-taking illusions.

---

## 3. The Dual-Engine Portfolio

```
                                 DATACATALYST
                                       │
        ┌──────────────────────────────┴──────────────────────────────┐
        ▼                                                             ▼
 TRACK A: AUTOMATED TECH ENGINE                TRACK B: SPECIALIZED OPERATIONS ENGINE
 (Software & Systems Engineering)              (Human-in-the-Loop & Data Ops)
 ├─ Automated VAD Slicer (Silero)              ├─ Multi-Speaker Audio Sourcing (48kHz)
 ├─ Async Benchmark Harness (WebSockets/HTTP)  ├─ Dual Transcription (Verbatim + Clean)
 ├─ Adversarial Evaluators (Cutoffs/Noise)     ├─ Speaker Diarization & Track Separation
 ├─ Acoustic Corruption & Telephony Simulator  ├─ Live Human Red-Team Callers
 └─ Continuous Voice CI/CD Regression Suite   └─ 100% Consent & DPDP/EU AI Act Compliance
```

---

## 4. Track A: Automated Tech & Systems Engineering

DataCatalyst builds automated testing and evaluation infrastructure to continuously benchmark and red-team Voice AI systems.

### 4.1 Automated Audio Slicing & Boundary Extraction (`extract_turns.py`)
* **Silero VAD Integration:** Utilizes high-precision Voice Activity Detection (VAD) to programmatically segment 20-minute, multi-speaker conversational sessions into targeted evaluation clips.
* **Boundary & Pause Cataloging:** Automatically identifies speaker turn boundaries, mid-thought thinking hesitations (100ms–800ms), conversational overlaps, and pure background noise intervals without human intervention.
* **Categorized Test Units:** Exports short, structured evaluation windows (e.g., 3s–8s clips ending at critical turn/pause thresholds) annotated with precise millisecond boundaries.

### 4.2 Adversarial API Stress-Test Runner (`benchmark_runner.py`)
* **Async Parallel Streaming:** Built on Python’s `asyncio`, `httpx`, and `websockets` to stream audio chunks in real-time or faster-than-real-time against commercial speech endpoints:
  * **OpenAI Realtime API:** WebSocket-based bidirection testing for audio-in/audio-out latency and server VAD behavior.
  * **Deepgram (Nova-2 / Flux):** Live transcription and turn-taking latency profiling.
  * **Sarvam AI:** Indic speech-to-text and speech-to-speech endpoint evaluation.
  * **ElevenLabs Conversational AI:** Interruption latency and turn-taking resilience.
* **Automated Failure Detectors:**
  * **Premature Cutoff Detector:** Flags instances where the target API emits a `speech_stopped` event or begins responding while the speaker was merely pausing (100ms–800ms) mid-utterance.
  * **Phantom Hallucination Detector:** Evaluates API output on pure silence, heavy breathing, dynamic mic pops, or ambient noise clips, flagging any non-empty text generation or bot initiation.
  * **Entity & Numeral Comparator:** Automatically matches extracted numbers, Indian financial values (lakhs, crores, rupees), phone numbers, and alphanumeric IDs against gold-standard JSON annotations.
  * **Latency Profiler:** Records millisecond-accurate metrics for Time-to-First-Token (TTFT), Voice-to-Voice end-of-turn latency, and round-trip transport time (RTT).

### 4.3 Acoustic Stress Injection (`stress_injector.py`)
* Programmatically applies real-world transmission impairments to pristine training/test audio:
  * VoIP packet loss and jitter simulation.
  * Telephony bandpass filtering and 8kHz downsampling (G.711 codec emulation).
  * Overlay of calibrated Indian acoustic environments (traffic, busy office, cafeteria, ceiling fan hum).
  * Dynamic microphone clipping and gain modulation.

### 4.4 Automated Failure Triage & CI/CD Suite (`reports/`)
* Automatically isolates failing test clips into a dedicated `failures/` directory.
* Emits structured JSON diagnostic reports containing timestamp deltas, audio waveforms, model responses, and error classifications.
* Operates headlessly as a Voice CI/CD gatekeeper to block regressions before production voicebot deployments.

---

## 5. Track B: Specialized Operations & Human Data Engine

The operational backbone of DataCatalyst delivers verified, gold-standard speech datasets and real-world human evaluation.

### 5.1 Proprietary Indian Conversational Speech Datasets
* **Native Conversational Audio:** Spontaneous 2-speaker dialogues and structured read-speech in Hindi and Hinglish (expanding across regional Indian languages).
* **Audio Specifications:**
  * Sample Rate: **48,000 Hz (48kHz)**
  * Bit Depth: **16-bit PCM Mono**
  * Frequency Response: **14–16 kHz preserved**
  * Recording Methodology: High-grade VoIP (WebRTC with dynamic microphones) capturing authentic conversational cadence while preserving acoustic separation.
* **Speaker Pool & Scalability:** Active core pool scalable from 10 to 50+ diverse speakers within 7 days, maintaining identical acoustic and QC standards.

### 5.2 Dual Ground-Truth Transcription
Every audio recording is paired with two distinct, complementary transcription layers:
1. **Verbatim Transcription:** Captures every uttered token precisely as spoken—including disfluencies, false starts, filler sounds (*umm*, *haan*, *achha*), repetitions, and laughter. Critical for acoustic model training and pause-boundary detection.
2. **Normalized Ground Truth:** Human-audited, grammatically and orthographically standardized transcriptions guaranteeing **<10% Word Error Rate (WER) / Character Error Rate (CER)**. Optimized for ASR semantic benchmarking and language model fine-tuning.

### 5.3 Speaker Separation & Diarization
* Delivery includes isolated individual speaker audio tracks alongside a synchronized merged conversation file.
* Full turn-level diarization metadata detailing speaker identifiers, turn start/end timestamps, and inter-speaker silence intervals.

### 5.4 Live Human Red-Teaming & "In-The-Wild" Calling
* Human evaluators conduct live telephone and WebRTC calls against client voicebots.
* Evaluators execute deliberate stress tactics: rapid interruptions, abrupt topic switching, mid-sentence language shifting, emotional inflection, and adversarial prompt injections.
* Delivers subjective Mean Opinion Score (MOS) evaluations measuring conversational naturalness, perceived latency, and tonal appropriateness.

### 5.5 Domain Customization & NLU Tagging
* Custom dataset creation for vertical enterprise domains:
  * **BFSI:** Loan inquiries, credit card verification, insurance claims, KYC dialogues.
  * **Healthcare:** Patient booking, symptom intake, pharmacy coordination.
  * **Logistics & E-Commerce:** Order tracking, delivery address resolution, return processing.
  * **Telecom & Customer Support:** Technical troubleshooting, plan upgrades, dispute resolution.
* Intent classification and slot tagging layers (NLU annotation) mapped directly to transcribed audio turns.

---

## 6. Consent, Ethics & Legal Framework

DataCatalyst enforces a strict **4-Stage Compliance Chain** for every second of recorded audio:

```
[1. Informed Contributor] ──► [2. Written Explicit Consent] ──► [3. Automated PII Redaction] ──► [4. Audit Documentation]
    Briefed on commercial        Signed, legally binding          All phone numbers, names,        Cryptographically linked
    AI / ML training use         release covering ML training      addresses & IDs scrubbed         records delivered to client
```

* **No Copyright or IP Exposure:** 100% original recordings with zero reliance on web scraping, YouTube rip-offs, or grey-market datasets.
* **Global Regulatory Alignment:** Fully compliant with **India's Digital Personal Data Protection (DPDP) Act 2023** and the **EU AI Act** requirements for traceable, consented high-risk AI training data.
* **Audit-Ready Documentation:** Every dataset shipment includes formal consent certificates and provenance records.

---

## 7. Licensing & Commercial Models

DataCatalyst operates flexible commercial structures tailored to enterprise needs:

| Model | Target Audience | Rights & Exclusivity | Customization |
| :--- | :--- | :--- | :--- |
| **Shared Access (Non-Exclusive)** | Academic labs, research teams, early-stage AI startups | Perpetual, commercial AI training license; non-exclusive catalog access | Standard catalog topics & speaker distributions |
| **Full Ownership (Exclusive Custom Build)** | Enterprise AI labs, Tier-1 foundation model builders, defense/BFSI | 100% exclusive ownership; dataset is never licensed or sold to any other entity | Fully tailored domain vocabulary, demographic split, recording scripts, and custom acoustic profiles |

---

## 8. Technical Infrastructure & Stack

* **Programming Language:** Python 3.10+
* **Concurrency & Networking:** `asyncio`, `httpx`, `websockets` (supporting high-throughput parallel streaming)
* **Audio & ML Tooling:** `torchaudio`, `librosa`, `soundfile`, `silero-vad`
* **Local Hardware Context:**
  * CPU: AMD Ryzen 7 5700X3D (8 Cores, 16 Threads)
  * Memory: 16 GB DDR4
  * GPU: NVIDIA GeForce RTX 3060 12GB VRAM (capable of local execution of Whisper, Faster-Whisper, and small judge models)
* **Web Platform & Cloud Stack:**
  * Frontend: Modern Vanilla HTML5 / CSS3 (dynamic OKLCH theming, Cabinet Grotesk / General Sans typography)
  * Hosting: AWS Amplify
  * API & Form Backend: AWS Lambda Function URL (`ap-south-1` region) integrated with direct email dispatchers and CORS preflight bypass.

---

## 9. Contact & Company Details

* **Website:** [https://datacatalyst.in](https://datacatalyst.in)
* **Founder & CEO:** Divyam Bhatia ([LinkedIn](https://www.linkedin.com/in/bhatia-divyam/))
* **Company LinkedIn:** [DataCatalyst on LinkedIn](https://www.linkedin.com/company/datacatalyst-tech)
* **Primary Contact:** [hello@datacatalyst.in](mailto:hello@datacatalyst.in)
* **Support:** [support@datacatalyst.in](mailto:support@datacatalyst.in)
* **Headquarters:** Sri Ganganagar, Rajasthan, India
