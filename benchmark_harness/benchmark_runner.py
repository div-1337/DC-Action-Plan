"""
DataCatalyst: Voice AI Adversarial Benchmark Runner
Executes Zero-Text Tests:
1. Phantom Noise & Breathing Hallucination Test
2. Premature Cutoff & Pause-Tolerance Test
"""

import os
import sys
import argparse
import json
import time
import asyncio
from pathlib import Path
import soundfile as sf
import httpx

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MockSpeechConnector:
    """Simulated provider to test the harness locally without burning API credits."""
    def __init__(self, name="mock_provider", hallucinate_prob=0.25, cutoff_threshold_ms=450):
        self.name = name
        self.hallucinate_prob = hallucinate_prob
        self.cutoff_threshold_ms = cutoff_threshold_ms

    async def test_silence(self, clip_path: Path) -> dict:
        t0 = time.time()
        await asyncio.sleep(0.1) # Simulate network RTT
        # Simulate occasional hallucination on Indian room noise
        has_hallucination = (hash(clip_path.name) % 4 == 0)
        emitted_text = "हाँ बोलिए" if has_hallucination else ""
        return {
            "provider": self.name,
            "clip": clip_path.name,
            "emitted_text": emitted_text,
            "latency_ms": round((time.time() - t0) * 1000, 1),
            "is_hallucination": bool(emitted_text)
        }

    async def test_hesitation(self, clip_path: Path, pause_ms: int) -> dict:
        t0 = time.time()
        await asyncio.sleep(0.15)
        # If the pause is longer than provider's cutoff threshold, it prematurely cuts off
        is_cutoff = pause_ms >= self.cutoff_threshold_ms
        return {
            "provider": self.name,
            "clip": clip_path.name,
            "pause_ms": pause_ms,
            "cutoff_threshold_ms": self.cutoff_threshold_ms,
            "premature_cutoff": is_cutoff,
            "latency_ms": round((time.time() - t0) * 1000, 1)
        }

class SarvamConnector:
    """Connector for Sarvam AI Speech-to-Text API."""
    def __init__(self, api_key: str = None):
        self.name = "sarvam_ai"
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        self.url = "https://api.sarvam.ai/speech-to-text"

    async def test_silence(self, clip_path: Path) -> dict:
        if not self.api_key:
            return {"provider": self.name, "error": "SARVAM_API_KEY not set"}
        
        t0 = time.time()
        async with httpx.AsyncClient() as client:
            with open(clip_path, "rb") as f:
                files = {"file": (clip_path.name, f, "audio/wav")}
                headers = {"api-subscription-key": self.api_key}
                data = {"language_code": "hi-IN", "model": "saaras:v2"}
                try:
                    resp = await client.post(self.url, headers=headers, files=files, data=data, timeout=15.0)
                    resp_json = resp.json()
                    transcript = resp_json.get("transcript", "").strip()
                    return {
                        "provider": self.name,
                        "clip": clip_path.name,
                        "emitted_text": transcript,
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "is_hallucination": len(transcript) > 0
                    }
                except Exception as e:
                    return {"provider": self.name, "clip": clip_path.name, "error": str(e)}

class DeepgramConnector:
    """Connector for Deepgram Live / Prerecorded ASR."""
    def __init__(self, api_key: str = None):
        self.name = "deepgram_nova2"
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY", "")
        self.url = "https://api.deepgram.com/v1/listen?model=nova-2&language=hi"

    async def test_silence(self, clip_path: Path) -> dict:
        if not self.api_key:
            return {"provider": self.name, "error": "DEEPGRAM_API_KEY not set"}
        t0 = time.time()
        async with httpx.AsyncClient() as client:
            with open(clip_path, "rb") as f:
                headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "audio/wav"}
                try:
                    resp = await client.post(self.url, headers=headers, content=f.read(), timeout=15.0)
                    resp_json = resp.json()
                    transcript = ""
                    channels = resp_json.get("results", {}).get("channels", [])
                    if channels and "alternatives" in channels[0]:
                        transcript = channels[0]["alternatives"][0].get("transcript", "").strip()
                    return {
                        "provider": self.name,
                        "clip": clip_path.name,
                        "emitted_text": transcript,
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "is_hallucination": len(transcript) > 0
                    }
                except Exception as e:
                    return {"provider": self.name, "clip": clip_path.name, "error": str(e)}

def log_failure(failure_type: str, result: dict, source_clip: Path, output_dir: Path):
    dest_dir = output_dir / failure_type
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy audio clip to failure triage folder
    import shutil
    dest_clip = dest_dir / source_clip.name
    if not dest_clip.exists():
        shutil.copy2(source_clip, dest_clip)

    # Save diagnostic JSON
    json_path = dest_dir / f"{source_clip.stem}_diagnostic.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "error_type": failure_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": result,
            "triage_audio": str(dest_clip)
        }, f, indent=2)

async def run_hallucination_benchmark(provider, clips, failures_dir: Path):
    print(f"\n--- RUNNING PHANTOM NOISE HALLUCINATION BENCHMARK [{provider.name}] ---")
    print(f"Total silence/noise clips to test: {len(clips)}")
    
    passed = 0
    failed = 0

    for idx, clip in enumerate(clips, 1):
        res = await provider.test_silence(clip)
        if res.get("is_hallucination"):
            failed += 1
            log_failure("phantom_hallucinations", res, clip, failures_dir)
            print(f"  [{idx}/{len(clips)}] [FAIL - HALLUCINATION] {clip.name} -> Generated: '{res.get('emitted_text')}' ({res.get('latency_ms')}ms)")
        elif res.get("error"):
            print(f"  [{idx}/{len(clips)}] [ERROR] {clip.name} -> {res.get('error')}")
        else:
            passed += 1
            print(f"  [{idx}/{len(clips)}] [PASS - SILENT] {clip.name} ({res.get('latency_ms')}ms)")

    total = passed + failed
    fail_rate = round((failed / max(total, 1)) * 100.0, 1)
    print(f"\nProvider: {provider.name} | Total: {total} | Pass: {passed} | Fail (Hallucinations): {failed} | Failure Rate: {fail_rate}%\n")

async def run_cutoff_benchmark(provider, clips_metadata, failures_dir: Path):
    print(f"\n--- RUNNING PREMATURE CUTOFF BENCHMARK [{provider.name}] ---")
    print(f"Total hesitation clips to test: {len(clips_metadata)}")

    passed = 0
    failed = 0

    for idx, meta in enumerate(clips_metadata, 1):
        clip_path = Path(meta["file_path"])
        pause_ms = meta["pause_duration_ms"]
        res = await provider.test_hesitation(clip_path, pause_ms)

        if res.get("premature_cutoff"):
            failed += 1
            log_failure("premature_cutoffs", res, clip_path, failures_dir)
            print(f"  [{idx}/{len(clips_metadata)}] [FAIL - PREMATURE CUTOFF] {clip_path.name} (Pause: {pause_ms}ms) -> Provider cut off at {res.get('cutoff_threshold_ms')}ms!")
        else:
            passed += 1
            print(f"  [{idx}/{len(clips_metadata)}] [PASS - TOLERATED] {clip_path.name} (Pause: {pause_ms}ms tolerated)")

    total = passed + failed
    fail_rate = round((failed / max(total, 1)) * 100.0, 1)
    print(f"\nProvider: {provider.name} | Total: {total} | Pass: {passed} | Fail (Cutoffs): {failed} | Cutoff Rate: {fail_rate}%\n")

async def main_async():
    parser = argparse.ArgumentParser(description="DataCatalyst Voice AI Adversarial Benchmark")
    parser.add_argument("--test", choices=["hallucination", "cutoff", "all"], default="all")
    parser.add_argument("--provider", choices=["mock", "sarvam", "deepgram"], default="mock")
    parser.add_argument("--clips-dir", type=str, default="test_clips")
    parser.add_argument("--failures-dir", type=str, default="reports/failures")
    args = parser.parse_args()

    clips_dir = Path(args.clips_dir)
    failures_dir = Path(args.failures_dir)

    # Initialize Provider
    if args.provider == "sarvam":
        provider = SarvamConnector()
    elif args.provider == "deepgram":
        provider = DeepgramConnector()
    else:
        provider = MockSpeechConnector(name="mock_speech_api")

    silence_clips = sorted(list((clips_dir / "ambient_silence").glob("*.wav")))
    
    # Load turn index for hesitations
    turn_index_path = Path("manifests/turn_index.json")
    hesitation_metas = []
    if turn_index_path.exists():
        with open(turn_index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for sess in data.get("sessions", []):
                for h in sess.get("clips", {}).get("hesitations", []):
                    if Path(h["file_path"]).exists():
                        hesitation_metas.append(h)

    print("\n=======================================================")
    print(" DataCatalyst Voice AI Adversarial Reliability Harness")
    print(f" Selected Provider: {provider.name}")
    print(f" Test Suite       : {args.test.upper()}")
    print("=======================================================\n")

    if args.test in ["hallucination", "all"] and silence_clips:
        await run_hallucination_benchmark(provider, silence_clips, failures_dir)

    if args.test in ["cutoff", "all"] and hesitation_metas:
        await run_cutoff_benchmark(provider, hesitation_metas, failures_dir)

    print("Benchmarking session complete. Any failures are triaged into reports/failures/\n")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
