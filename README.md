# WhisperX Transcription Assessment

This repository contains a focused Python implementation of an audio/video transcription pipeline using **FastAPI**, **FFmpeg/FFprobe** and **WhisperX**.

The implementation is intentionally scoped for an engineering assessmen which demonstrates media validation, format normalization, speech-to-text transcription, segment-level timestamps, long-form audio handling, temporary-file cleanup, bounded retry behavior and JSON output. It does not include a database, permanent media storage, a production task queue, authentication or concurrent transcription workers.

## 1. Problem Statement

Build a simple transcription pipeline that:

- accepts an audio or video file
- handles common media formats
- transcribes spoken language into text
- returns timestamps for each transcript segment
- supports long recordings
- handles processing failures sensibly
- run and review locally on CPU.

## 2. Implemented Technology Stack

- **Python 3.10/3.11** for the application.
- **FastAPI** for the optional multipart upload demonstration.
- **FFprobe** for media inspection and audio-stream validation.
- **FFmpeg** for audio extraction, decoding and normalization.
- **WhisperX** for transcription.
- **Faster-Whisper** used internally by WhisperX for efficient inference.
- **Voice Activity Detection (VAD)** through the WhisperX pipeline for speech-aware long-form processing.
- **JSON** as the canonical result format.

## 3. Scope of the Implementation

### Included

- Local command-line transcription of audio or video files.
- Optional synchronous FastAPI multipart endpoint.
- FFprobe validation before model inference.
- FFmpeg extraction of the first audio stream.
- Conversion to 16 kHz mono PCM WAV.
- WhisperX transcription on CPU or CUDA.
- Segment-level `start`, `end` and `text` fields.
- Automatic language detection or an explicit language hint.
- VAD-based handling of long recordings.
- Temporary normalized-audio cleanup.
- Bounded retry attempts for transient runtime failures.
- Atomic JSON result writing.

### Intentionally excluded

- Database storage.
- Permanent storage of uploaded audio.
- Permanent transcript storage beyond the requested output JSON.
- Concurrent transcription processing.
- Authentication and authorization.
- Speaker diarization.
- Word-level forced alignment.

These exclusions keep the submission focused on the assessment core transcription workflow.

## 4. Repository Contents

```text
.
├── transcribe.py
├── requirements.txt
└── README.md
```

- `transcribe.py` contains the media validation, normalization, transcription, retry, JSON serialization, CLI and optional FastAPI logic.
- `requirements.txt` contains the required Python packages.
- `README.md` explains the implemented design and engineering decisions.

## 5. Pipeline Architecture

```text
Local audio/video file
        |
        v
Extension pre-check
        |
        v
FFprobe inspection
  - confirm audio stream
  - detect container and codec
  - read duration, channels, and sample rate
        |
        v
FFmpeg normalization
  - select first audio stream
  - remove video
  - convert to mono
  - resample to 16 kHz
  - write temporary PCM WAV
        |
        v
WhisperX transcription
  - Faster-Whisper inference
  - language detection or language hint
  - VAD-based long-form processing
  - segment timestamps
        |
        v
Result normalization
  - id
  - start
  - end
  - text
        |
        v
Atomic JSON output
        |
        v
Temporary WAV cleanup
```

## 6. Design Decision: FastAPI Multipart Upload

The primary implementation is a local CLI because the assessment version does not require a production API. A small FastAPI mode is included to demonstrate the selected multipart-upload approach without introducing database or queue infrastructure.

FastAPI `UploadFile` was selected because multipart upload is a standard mechanism supported by browsers, command-line tools and API clients. The endpoint reads the uploaded file in 1 MB blocks instead of reading the complete request body into memory.

The optional API is synchronous by design:

```text
POST /transcribe
    -> temporary upload
    -> validation and normalization
    -> transcription
    -> JSON file response
```

This is appropriate only for a local demonstration. A production implementation should persist the upload, create a job, return `202 Accepted` and run transcription in a controlled background worker.

## 7. Design Decision: FFprobe and FFmpeg

### Why FFprobe is used

The script does not trust the file extension or client-provided media type. A file named `recording.mp3` might contain a different container, an unsupported codec, corrupt content or no audio stream.

FFprobe inspects the actual media and returns:

- container name
- codec name
- audio sample rate
- channel count
- duration
- file size

The script rejects media that cannot be inspected or does not contain a decodable audio stream.

### Why FFmpeg is used

FFmpeg provides one common decoding and normalization path for different containers and codecs. The application therefore does not need separate Python logic for WAV, MP3, M4A, AAC, WebM, MP4, MOV, MKV and other formats.

The implemented normalization is equivalent to:

```powershell
ffmpeg -y -v error `
  -i input_file `
  -map 0:a:0 `
  -vn `
  -ac 1 `
  -ar 16000 `
  -c:a pcm_s16le `
  normalized.wav
```

The options mean:

- `-map 0:a:0`: select the first audio stream;
- `-vn`: exclude video;
- `-ac 1`: convert to mono;
- `-ar 16000`: resample to 16 kHz; and
- `-c:a pcm_s16le`: create 16-bit PCM audio.

The normalized WAV exists only inside a temporary directory and is automatically removed after success or failure.

### Supported formats

The script recognizes common extensions including:

```text
.wav .mp3 .flac .m4a .aac .ogg .oga .opus
.wma .amr .aif .aiff .webm .mp4 .mov .mkv
.avi .wmv .flv .mpeg .mpg .3gp .m4v
```

The extension set is an early usability check. Actual support depends on the codecs and demuxers available in the installed FFmpeg build. Unknown extensions are still probed allowing valid media to be processed when FFmpeg can decode it.

## 8. Design Decision: WhisperX

WhisperX was selected as the transcription layer because it provides:

- Whisper-family multilingual speech recognition
- Faster-Whisper inference
- VAD-based speech segmentation
- batched transcription
- segment timestamps
- a future upgrade path to word alignment and speaker diarization.

The implemented call uses:

```python
result = model.transcribe(
    audio,
    batch_size=batch_size,
    language=language,
)
```

The script converts the returned segments into a stable assessment response containing only the fields required by the task:

```json
{
  "id": 0,
  "start": 2.782,
  "end": 20.753,
  "text": "Example transcribed segment."
}
```

## 9. Segment Timestamps

The assessment asks for timestamps per segment.

A segment timestamp covers a phrase or speech block:

```json
{
  "start": 2.782,
  "end": 20.753,
  "text": "A complete phrase or speech block."
}
```

The implementation deliberately does not call WhisperX forced alignment because word timestamps are not required. This avoids loading an additional language-specific alignment model, reduces memory use and shortens processing time.

The JSON metadata makes this decision explicit:

```json
{
  "vad_enabled": true,
  "word_alignment_enabled": false
}
```

## 10. Handling Long Audio and Video Files

### Implemented approach

The script uses WhisperX VAD and batched long-form transcription rather than manually creating fixed 30-second files.

The workflow is:

1. FFmpeg creates one normalized 16 kHz mono WAV.
2. WhisperX loads the normalized audio.
3. VAD identifies speech-active regions.
4. WhisperX/Faster-Whisper processes the speech in batches.
5. Returned timestamps remain on the original normalized-audio timeline.
6. The script writes ordered segments to JSON.

### Why this approach was selected

VAD-based processing is preferable to arbitrary fixed-size cutting because it follows speech boundaries and avoids unnecessary processing of long silence. It also avoids custom logic for:

- cutting WAV files
- creating overlapping chunks
- correcting timestamps with chunk offsets
- removing repeated text at overlap boundaries
- merging a large collection of temporary chunk files.

This is sufficient for the local assessment implementation and was verified with a video lasting approximately 14 minutes and 23 seconds.

### Production extension

For multi-hour recordings or distributed workers the next step would be explicit chunk manifests and checkpointing:

```text
chunk start/end offset
    -> per-chunk status
    -> per-chunk transcript
    -> offset adjustment
    -> chronological merge
```

That production extension is not required by the present implementation because no queue, database or permanent partial-result storage is included.

## 11. Failure Handling and Retry Behavior

The script performs validation before starting expensive inference:

- checks that the source path exists
- verifies that FFprobe and FFmpeg are on `PATH`
- confirms a decodable audio stream
- checks FFmpeg's exit status
- confirms that FFmpeg produced a non-empty normalized WAV

WhisperX runtime failures represented by `RuntimeError` or `OSError` are retried a bounded number of times with a short exponential delay.

Default behavior:

```text
initial attempt
retry after 1 second
retry after 2 seconds
stop and report the final failure
```

Retries are intentionally bounded. Invalid media and FFmpeg validation failures are not repeatedly retried because processing the same invalid input is unlikely to succeed.

The implemented retry behavior was exercised during the Windows test. The first model-cache operation encountered a symlink privilege error, the script retried and the second attempt completed successfully.

## 12. JSON Output

The canonical output contains source metadata, transcription results and processing configuration.

```json
{
  "schema_version": "1.0",
  "source": {
    "filename": "2.mp4",
    "format": "mov,mp4,m4a,3gp,3g2,mj2",
    "duration_seconds": 863.271,
    "size_bytes": 54158336,
    "audio_stream": {
      "codec_name": "aac",
      "codec_type": "audio",
      "sample_rate": "44100",
      "channels": 2
    }
  },
  "transcription": {
    "language": "en",
    "text": "Complete transcript text...",
    "segments": [
      {
        "id": 0,
        "start": 2.782,
        "end": 20.753,
        "text": "First transcript segment..."
      }
    ]
  },
  "processing": {
    "engine": "whisperx",
    "model": "small",
    "device": "cpu",
    "compute_type": "int8",
    "batch_size": 2,
    "vad_enabled": true,
    "word_alignment_enabled": false,
    "elapsed_seconds": 143.531
  }
}
```

The result is written atomically. The script first writes `<output>.tmp` and then replaces the final output path. This reduces the risk of leaving a partially written JSON file if serialization or disk writing fails.

## 13. Verified Local Test

The implementation was tested on Windows from:

```text
C:\volga\Whisperx
```

Input:

```text
2.mp4
```

Command:

```powershell
python transcribe.py "2.mp4" `
  --model small `
  --device cpu `
  --compute-type int8 `
  --batch-size 2
```

Observed result:

- WhisperX `small` model loaded on CPU.
- Compute type: `int8`.
- Language detected as English.
- FFprobe identified AAC stereo audio at 44.1 kHz.
- Source duration: approximately 863 seconds.
- JSON output: `2.transcript.json`.
- Output contained ordered segment-level timestamps.
- Final transcript covered the recording through approximately 862 seconds.
- Model-reported processing time was approximately 144 seconds, excluding part of the first model-download setup.

The output therefore satisfies the required contract:

```text
media input
    -> transcript text
    -> JSON
    -> start/end timestamp per segment
```

## 14. Installation on Windows

### Prerequisites

- Python 3.10 or 3.11.
- FFmpeg and FFprobe installed and available on `PATH`.
- Internet access for the first model download.

Verify FFmpeg:

```powershell
ffmpeg -version
ffprobe -version
```

Create and activate an environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If using Conda:

```powershell
conda activate volga
pip install -r requirements.txt
```

## 15. Engineering Trade-offs

### WhisperX versus Faster-Whisper directly

Faster-Whisper alone can return segment timestamps with fewer dependencies. WhisperX was retained because it matches the selected assessment stack and provides an upgrade path to forced word alignment and diarization. Those extra stages remain disabled.

### Normalize every input versus direct decoding

Direct PyAV decoding can avoid creation of a temporary WAV. Explicit FFmpeg normalization was chosen because it provides predictable model input, clearer validation failures and consistent behavior for audio extracted from video containers.

### CLI versus API

The CLI is the primary implemented interface because the assessment does not require API deployment. The optional FastAPI mode demonstrates multipart upload without adding production infrastructure.

### One logical long-form input versus explicit chunk files

WhisperX VAD and batching were selected for the local implementation. Explicit chunk files and checkpointing would be added only when distributed processing, progress persistence or chunk-level recovery becomes necessary.

### Model size

The `small` model offers a practical CPU balance between transcription quality, memory use and processing speed. A larger model may improve technical-term recognition but requires more memory and processing time.


## 16. Production Evolution

If the assessment were extended into a production service, the next architecture would be:

```text
FastAPI multipart upload
    -> private object storage
    -> database job record
    -> Celery/RabbitMQ or Redis queue
    -> bounded CPU/GPU worker pool
    -> chunk checkpoints for long audio
    -> canonical transcript JSON
    -> status and result endpoints
```

Production additions would include:

- `202 Accepted` asynchronous jobs;
- PostgreSQL job metadata;
- object storage for audio and transcripts;
- idempotency keys;
- bounded concurrent inference;
- classified retry policies;
- chunk-level recovery;
- authentication and tenant authorization;
- retention policies;
- metrics, logs, tracing, and alerting.

**Some relevant points related to Assesment question whihc are not implemented in current script.** 

## 17. Long Audio Files

### Selected approach

Process long files as asynchronous transcription jobs, use VAD to create speech-aware chunks, transcribe the chunks through WhisperX's Faster-Whisper backend, preserve each chunk's original time offset and merge the resulting segments into one timestamped transcript.

### Why asynchronous processing

A long recording can take minutes or hours to process. Holding an HTTP connection open creates avoidable problems:

- gateway or client timeouts
- occupied API workers
- poor progress visibility
- expensive full-job retries
- difficult cancellation and recovery
- resource exhaustion during traffic bursts.

The API should therefore persist the upload, enqueue the job and return `202 Accepted` with a job ID.

### Why VAD-based chunking

Voice Activity Detection splits around silence or low-speech regions. This is preferable to blindly cutting every fixed number of seconds because it reduces mid-word and mid-sentence boundaries and avoids spending model time on long silence.

Suggested starting policy:

```text
target speech chunk:       20-30 seconds
maximum speech chunk:      about 30 seconds
minimum split silence:     500-1000 ms
speech padding:            200-400 ms
```

These values must remain configurable and should be tuned with representative recordings.


### Merge process

1. Save a manifest containing every chunk's original start/end offset.
2. Transcribe pending chunks.
3. Add the original chunk offset to every returned segment.
4. Sort all segments by global start time.
5. Remove duplicated boundary text if overlap was used.
6. Join segment text to create the complete transcript.
7. Write the final JSON atomically.

### Checkpointing

Store partial output per chunk. If chunk 19 fails after chunks 1-18 complete retry chunk 19 only. This substantially reduces recovery cost for multi-hour recordings.


## 18. Concurrent Uploads

### Decision

Separate **upload concurrency** from **transcription concurrency**.

- FastAPI handles multiple I/O-bound uploads.
- Each upload is streamed to storage in bounded chunks.
- Every accepted upload creates a durable job.
- Celery with Redis or RabbitMQ queues inference work.
- A small, controlled worker pool runs WhisperX.

Do not start one model inference operation for every incoming upload. Inference concurrency must match available CPU, RAM, GPU and VRAM.


The queue provides backpressure. When queue depth or storage capacity reaches a configured threshold the API should return `429 Too Many Requests` or `503 Service Unavailable` with `Retry-After` rather than accepting unbounded work.

## 19. Retry and Failure Recovery

#### Transient failures: retry

- temporary database, broker, or storage timeout
- temporary network failure
- worker interruption
- recoverable service unavailability

Use bounded exponential backoff with jitter for example:

```text
attempt 1: immediate
attempt 2: about 10 seconds
attempt 3: about 30 seconds
attempt 4: about 90 seconds
then: retry exhausted
```

#### Resource failures: retry with a safer profile

- out-of-memory error
- batch size too large
- chunk too long.

Retrying the same resource configuration is unlikely to help.

#### Permanent failures: do not retry automatically

- corrupt or unsupported media
- no audio stream
- invalid parameters
- missing original object
- duration or size limit exceeded
- authentication or authorization failure.

### Idempotency

Queue delivery is treated as at-least-once. Workers must be idempotent:

1. atomically claim an eligible job
2. return the existing result if the job is already complete
3. use one predictable result key per transcript version
4. write results to a temporary object first
5. publish final output atomically
6. update the database only after the result is valid

Support an `Idempotency-Key` request header so a client retry does not create a duplicate transcription job.

### Worker crash recovery

Use late acknowledgement only with idempotent tasks. If a worker exits before completion the broker can redeliver the unacknowledged job. Track attempts in the database and stop automatic delivery after the retry budget is exhausted.

### Long-audio recovery

Maintain status per chunk:

```text
PENDING -> PROCESSING -> COMPLETED
                     -> RETRY_SCHEDULED
                     -> FAILED
```

Persist each completed chunk's JSON. Resume from failed or pending chunks after a worker restart.

### Dead-letter/manual review

Jobs that exceed their retry budget move to `RETRY_EXHAUSTED`. Keep the original audio, error classification, attempt history, processing profile and last completed chunk so an authorized operator can retry safely.

## 20. REST API Design

### Create a transcription

```http
POST /api/v1/transcriptions
Authorization: Bearer <token>
Idempotency-Key: <unique-key>
Content-Type: multipart/form-data
```

Response:

```http
HTTP/1.1 202 Accepted
Location: /api/v1/transcriptions/{job_id}
Retry-After: 5
```

```json
{
  "job_id": "8595818c-cc7f-404c-a776-a504c625e231",
  "status": "queued",
  "status_url": "/api/v1/transcriptions/8595818c-cc7f-404c-a776-a504c625e231",
  "result_url": "/api/v1/transcriptions/8595818c-cc7f-404c-a776-a504c625e231/result"
}
```

### Suggested endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/transcriptions` | Upload media and create a job |
| `GET` | `/api/v1/transcriptions/{job_id}` | Retrieve status and progress |
| `GET` | `/api/v1/transcriptions/{job_id}/result` | Retrieve completed transcript |
| `POST` | `/api/v1/transcriptions/{job_id}/retry` | Retry an eligible failed job |
| `DELETE` | `/api/v1/transcriptions/{job_id}` | Cancel or delete a job |
| `GET` | `/health/live` | Process liveness |
| `GET` | `/health/ready` | Database, queue, and storage readiness |

### Job states

```text
UPLOADING
QUEUED
PROCESSING
RETRY_SCHEDULED
COMPLETED
FAILED
RETRY_EXHAUSTED
CANCELLED
DELETED
```

### Status response

```json
{
  "job_id": "8595818c-cc7f-404c-a776-a504c625e231",
  "status": "processing",
  "progress_percent": 42.5,
  "processed_duration_seconds": 263.0,
  "total_duration_seconds": 618.4,
  "attempt_count": 1,
  "error": null
}
```

### Error structure

```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA",
    "message": "The uploaded file does not contain a decodable audio stream.",
    "request_id": "req_923cf4a7"
  }
}
```

Recommended HTTP codes:

- `202`: accepted and queued;
- `400`: invalid option;
- `401`/`403`: authentication or authorization failure;
- `404`: job not found or not visible;
- `409`: operation conflicts with current job state;
- `413`: upload exceeds size limit;
- `415`: invalid or unsupported media;
- `422`: request validation failure;
- `429`: user rate or queue limit exceeded;
- `503`: service lacks temporary capacity.

FastAPI automatically exposes OpenAPI documentation, normally through `/docs`, `/redoc`, and `/openapi.json`, which makes the assessment easy to run and review.


## 21. Final Design Summary

The implemented pipeline is:

```text
FastAPI multipart upload or local file
    -> FFprobe validation
    -> FFmpeg decoding and 16 kHz mono normalization
    -> WhisperX/Faster-Whisper transcription with VAD
    -> segment-level timestamps
    -> atomic JSON output
    -> automatic temporary-file cleanup
```

This design cleanly separates media handling from speech recognition. FFmpeg is responsible for heterogeneous media inputs WhisperX is responsible for transcription and the Python application is responsible for validation, retries, result shaping and cleanup.

