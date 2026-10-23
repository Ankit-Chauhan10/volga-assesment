from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import whisperx
except ImportError as exc:
    raise SystemExit("WhisperX is not installed. Run: pip install -r requirements.txt") from exc

LOG = logging.getLogger("transcription")
MODEL_LOCK = threading.Lock()  
ALLOWED_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".oga", ".opus",
    ".wma", ".amr", ".aif", ".aiff", ".webm", ".mp4", ".mov", ".mkv",
    ".avi", ".wmv", ".flv", ".mpeg", ".mpg", ".3gp", ".m4v",
}


class TranscriptionError(RuntimeError):
    """Base error for a user-facing transcription failure."""


class InvalidMediaError(TranscriptionError):
    """Input is missing, unsupported, corrupt, or contains no audio stream."""


class ExternalToolError(TranscriptionError):
    """FFmpeg or FFprobe failed."""


@dataclass(frozen=True)
class Settings:
    model_name: str = os.getenv("WHISPER_MODEL", "small")
    device: str = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    batch_size: int = int(os.getenv("WHISPER_BATCH_SIZE", "4"))
    language: Optional[str] = os.getenv("WHISPER_LANGUAGE") or None
    max_retries: int = int(os.getenv("TRANSCRIPTION_MAX_RETRIES", "2"))
    ffmpeg_timeout_seconds: int = int(os.getenv("FFMPEG_TIMEOUT_SECONDS", "7200"))


class TranscriptionService:
    """Validates, normalizes, and transcribes one media file at a time."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: Any = None

    def load_model(self) -> None:
        if self._model is None:
            LOG.info(
                "Loading WhisperX model=%s device=%s compute_type=%s",
                self.settings.model_name,
                self.settings.device,
                self.settings.compute_type,
            )
            self._model = whisperx.load_model(
                self.settings.model_name,
                self.settings.device,
                compute_type=self.settings.compute_type,
                language=self.settings.language,
            )

    @staticmethod
    def _require_executable(name: str) -> str:
        executable = shutil.which(name)
        if not executable:
            raise ExternalToolError(
                f"{name} was not found on PATH. Install FFmpeg and reopen the terminal."
            )
        return executable

    def probe(self, source: Path) -> dict[str, Any]:
        ffprobe = self._require_executable("ffprobe")
        command = [
            ffprobe, "-v", "error", "-select_streams", "a:0",
            "-show_entries",
            "stream=index,codec_name,codec_type,sample_rate,channels,duration",
            "-show_entries", "format=format_name,duration,size",
            "-of", "json", str(source),
        ]
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=60, check=False
        )
        if completed.returncode != 0:
            raise InvalidMediaError(completed.stderr.strip() or "FFprobe could not read the media.")
        try:
            metadata = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise InvalidMediaError("FFprobe returned invalid metadata.") from exc
        if not metadata.get("streams"):
            raise InvalidMediaError("The file does not contain a decodable audio stream.")
        return metadata

    def normalize(self, source: Path, destination: Path) -> None:
        ffmpeg = self._require_executable("ffmpeg")
        command = [
            ffmpeg, "-y", "-v", "error", "-i", str(source),
            "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(destination),
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.settings.ffmpeg_timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise ExternalToolError(completed.stderr.strip() or "FFmpeg normalization failed.")
        if not destination.exists() or destination.stat().st_size == 0:
            raise ExternalToolError("FFmpeg produced no normalized audio.")

    @staticmethod
    def _segment_json(raw_segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        clean: list[dict[str, Any]] = []
        for index, segment in enumerate(raw_segments):
            text = str(segment.get("text", "")).strip()
            if not text:
                continue
            clean.append({
                "id": index,
                "start": round(float(segment.get("start", 0.0)), 3),
                "end": round(float(segment.get("end", 0.0)), 3),
                "text": text,
            })
        return clean

    def _transcribe_once(self, normalized_audio: Path, language: Optional[str]) -> dict[str, Any]:
        self.load_model()
        audio = whisperx.load_audio(str(normalized_audio))
        with MODEL_LOCK:
            result = self._model.transcribe(
                audio,
                batch_size=max(1, self.settings.batch_size),
                language=language or self.settings.language,
            )
        segments = self._segment_json(result.get("segments", []))
        return {
            "language": result.get("language") or language,
            "text": " ".join(part["text"] for part in segments),
            "segments": segments,
        }

    def transcribe(self, source_path: str | Path, output_path: str | Path) -> Path:
        source = Path(source_path).expanduser().resolve()
        output = Path(output_path).expanduser().resolve()
        if not source.is_file():
            raise InvalidMediaError(f"Input file not found: {source}")
        if source.suffix.lower() not in ALLOWED_EXTENSIONS:
            LOG.warning("Extension %s is not in the common-format allowlist; probing anyway.", source.suffix)

        metadata = self.probe(source)
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="transcription_") as temp_dir:
            normalized = Path(temp_dir) / "normalized.wav"
            self.normalize(source, normalized)
            last_error: Optional[Exception] = None
            attempts = max(1, self.settings.max_retries + 1)
            for attempt in range(1, attempts + 1):
                try:
                    result = self._transcribe_once(normalized, self.settings.language)
                    break
                except (RuntimeError, OSError) as exc:
                    last_error = exc
                    if attempt >= attempts:
                        raise TranscriptionError(
                            f"Transcription failed after {attempt} attempt(s): {exc}"
                        ) from exc
                    delay = min(30, 2 ** (attempt - 1))
                    LOG.warning("Attempt %d failed: %s. Retrying in %ds.", attempt, exc, delay)
                    gc.collect()
                    time.sleep(delay)
            else:  
                raise TranscriptionError(str(last_error))

        payload = {
            "schema_version": "1.0",
            "source": {
                "filename": source.name,
                "format": metadata.get("format", {}).get("format_name"),
                "duration_seconds": _to_float(metadata.get("format", {}).get("duration")),
                "size_bytes": _to_int(metadata.get("format", {}).get("size")),
                "audio_stream": metadata.get("streams", [{}])[0],
            },
            "transcription": result,
            "processing": {
                "engine": "whisperx",
                "model": self.settings.model_name,
                "device": self.settings.device,
                "compute_type": self.settings.compute_type,
                "batch_size": self.settings.batch_size,
                "vad_enabled": True,
                "word_alignment_enabled": False,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
            },
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = output.with_suffix(output.suffix + ".tmp")
        temporary_output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary_output.replace(output)
        return output


def _to_float(value: Any) -> Optional[float]:
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def default_output(source: Path) -> Path:
    return source.with_name(f"{source.stem}.transcript.json")


def build_fastapi_app(service: TranscriptionService):
    try:
        from fastapi import FastAPI, File, HTTPException, UploadFile
        from fastapi.responses import FileResponse
    except ImportError as exc:
        raise SystemExit("FastAPI dependencies are missing. Install requirements.txt") from exc

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        service.load_model()
        yield

    app = FastAPI(title="Local WhisperX Transcription Assessment", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/transcribe")
    async def transcribe_upload(file: UploadFile = File(...)):
        suffix = Path(file.filename or "upload.bin").suffix
        request_id = uuid.uuid4().hex
        request_dir = Path(tempfile.gettempdir()) / f"whisperx_{request_id}"
        request_dir.mkdir(parents=True, exist_ok=True)
        source = request_dir / f"input{suffix}"
        output = request_dir / "transcript.json"
        try:
            with source.open("wb") as target:
                while chunk := await file.read(1024 * 1024):
                    target.write(chunk)
            await file.close()
            service.transcribe(source, output)
            return FileResponse(output, media_type="application/json", filename="transcript.json")
        except InvalidMediaError as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except TranscriptionError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize media with FFmpeg and transcribe with WhisperX.")
    parser.add_argument("input", nargs="?", help="Local audio/video file path")
    parser.add_argument("--output", "-o", help="JSON output path")
    parser.add_argument("--model", default=os.getenv("WHISPER_MODEL", "small"))
    parser.add_argument("--device", choices=["cpu", "cuda"], default=os.getenv("WHISPER_DEVICE", "cpu"))
    parser.add_argument("--compute-type", default=os.getenv("WHISPER_COMPUTE_TYPE", "int8"))
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("WHISPER_BATCH_SIZE", "4")))
    parser.add_argument("--language", default=os.getenv("WHISPER_LANGUAGE") or None)
    parser.add_argument("--serve", action="store_true", help="Run optional FastAPI demo on localhost")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_args()
    settings = Settings(
        model_name=args.model,
        device=args.device,
        compute_type=args.compute_type,
        batch_size=max(1, args.batch_size),
        language=args.language,
    )
    service = TranscriptionService(settings)

    if args.serve:
        import uvicorn
        uvicorn.run(build_fastapi_app(service), host=args.host, port=args.port)
        return 0

    if not args.input:
        print("Input file is required unless --serve is used.", file=sys.stderr)
        return 2

    source = Path(args.input)
    output = Path(args.output) if args.output else default_output(source)
    try:
        written = service.transcribe(source, output)
        print(f"Transcript written to: {written}")
        return 0
    except TranscriptionError as exc:
        LOG.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
