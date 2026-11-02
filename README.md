# WhisperX Transcription Assessment

## Overview

This repository contains a focused Python implementation and production oriented system design for an audio/video transcription pipeline built with **FastAPI**, **FFprobe/FFmpeg** and **WhisperX**.

The implemented script demonstrates: -

- local audio/video input 
- optional FastAPI multipart upload
- media validation with FFprobe
- audio extraction and normalization with FFmpeg
- speech to text transcription with WhisperX
- segmentlevel timestamps
- long form processing with Voice Activity Detection (VAD)
- structured JSON output
- temporary- file cleanup
- bounded retry behavior
- CPU-friendly execution on Windows

The repository also documents how the same pipeline should evolve into a real world asynchronous service with object storage, durable queues, controlled workers, checkpoint recovery and a versioned REST API.

---

## 1. Assessment Requirements

### Part 1: Transcription Pipeline

The implemented solution must -

1. Accept an audio or video file.
2. Transcribe spoken language into text.
3. Return timestamps for each transcript segment.
4. Handle different media formats.
5. Handle long recordings.

### Part 2: Production System Design

The design must explain -

1. How concurrent uploads would be handled.
2. How audio and transcripts would be stored.
3. How failed transcriptions would be retried or recovered.
4. How the service would be exposed as an API.

---

## 2. Implemented Technology Stack

- **Python 3.10/3.11** for the application.
- **FastAPI** for the optional multipart upload demonstration.
- **FFprobe** for media inspection and audio stream validation.
- **FFmpeg** for media decoding, audio extraction and normalization.
- **WhisperX** for speech to text processing.
- **Faster-Whisper**  used internally by WhisperX for efficient inference.
- **Voice Activity Detection (VAD)** for speech aware long form processing.
- **JSON** as the canonical transcript format.

### Tested local configuration

```text
Operating system: Windows
Model:            small
Device:           CPU
Compute type:     int8
Batch size:       2
Language:         Automatically detected
```

---

## 3. Scope

### Implemented

- Local command line transcription of audio and video files.
- Optional synchronous FastAPI multipart endpoint.
- FFprobe validation before inference.
- FFmpeg extraction of the first audio stream.
- Conversion to 16 kHz mono 16-bit PCM WAV.
- WhisperX transcription on CPU or CUDA.
- Automatic language detection or an explicit language hint.
- Segment-level `id`, `start`, `end`, and `text` fields.
- VAD-based long-form processing.
- Temporary normalized audio cleanup.
- Bounded retries for selected runtime failures.
- Atomic JSON output writing.

### Intentionally not implemented in the assessment script

- Database storage.
- Permanent upload storage.
- Production message queue.
- Concurrent model inference.
- Authentication and authorization.
- Speaker diarization.
- Word-level forced alignment.
- Distributed chunk processing.

These are described in the production system design sections rather than included in the focused local implementation.

---

## 4. Repository Contents

```text
.
├── transcribe.py
├── requirements.txt
└── README.md
```

- `transcribe.py`: validation, normalization, transcription, retry handling, JSON serialization, CLI and optional FastAPI logic.
- `requirements.txt`: Python dependencies.
- `WINDOWS_SETUP.md`: local Windows setup and execution instructions.
- `README.md`: implementation details, design decisions and production-system design.

---

# Part 1: Implemented Transcription Pipeline

## 6. Accepting an Audio or Video File

The primary implementation is a Python command line script that accepts a local audio or video path. An optional FastAPI endpoint demonstrates accepting a file through `multipart/form-data` using `UploadFile`.

Example CLI execution:

```powershell
python transcribe.py "2.mp4" `
  --model small `
  --device cpu `
  --compute-type int8 `
  --batch-size 2
```

The optional endpoint reads the upload in bounded 1 MB chunks rather than loading the complete request body into memory.

Before transcription the pipeline:

1. Confirms that the local source exists.
2. Performs an initial extension check.
3. Confirms that `ffprobe` and `ffmpeg` are available on `PATH`.
4. Uses FFprobe to inspect the actual file.
5. Confirms that at least one decodable audio stream exists.
6. Uses FFmpeg to create normalized temporary audio.
7. Automatically removes temporary data after processing.

The filename, extension and MIME type are treated only as hints. The final media decision is based on the contents reported by FFprobe.

### Why this design

- The CLI is easy for a reviewer to run locally.
- The optional FastAPI interface demonstrates standard multipart upload handling.
- Both interfaces reuse the same `TranscriptionService` rather than duplicating business logic.
- Temporary processing avoids requiring a database or permanent storage for the assessment.

---

## 7. Transcribing Spoken Language into Text

WhisperX is used as the transcription engine. WhisperX uses Faster-Whisper internally and supports multilingual recognition, automatic language detection, VAD and batched inference.

The transcription flow is:

```text
Normalized audio
    -> WhisperX audio loading
    -> Voice Activity Detection
    -> Faster-Whisper inference
    -> language, text and segments
```

The model is loaded lazily and reused within the process. This avoids unnecessary model initialization for repeated operations in the same process.

The user can provide a language hint:

```powershell
python transcribe.py "2.mp4" --language en
```

If no language is supplied, WhisperX detects it automatically.

### Why the `small` model, CPU, and `int8`

The default assessment configuration is intended to run without dedicated GPU hardware:

- `small` gives a practical balance between speed and accuracy.
- `cpu` maximizes portability.
- `int8` reduces memory and compute requirements.
- batch size remains configurable to balance throughput and memory use.

A production deployment could select larger models and CUDA workers according to latency, accuracy and infrastructure requirements.

---

## 8. Segment-Level Timestamp Output

The final JSON contains the complete transcript and an ordered `segments` array. Each segment includes:

- `id`;
- `start` time in seconds;
- `end` time in seconds; and
- transcribed `text`.

Example:

```json
{
  "language": "en",
  "text": "Complete transcript text.",
  "segments": [
    {
      "id": 0,
      "start": 2.782,
      "end": 20.753,
      "text": "First transcribed segment."
    },
    {
      "id": 1,
      "start": 20.753,
      "end": 48.091,
      "text": "Second transcribed segment."
    }
  ]
}
```

The script removes empty entries, trims text, assigns sequential IDs and rounds timing values to three decimal places.

### Segment timestamps versus word timestamps

A segment timestamp covers a phrase or speech region. A word timestamp assigns separate timing to every word.

WhisperX forced alignment is deliberately disabled because the assessment requires segment timestamps only. Disabling alignment:

- avoids loading another language-specific model
- reduces memory use
- reduces processing time
- keeps the implementation focused on the required output

The output records this explicitly:

```json
{
  "vad_enabled": true,
  "word_alignment_enabled": false
}
```

JSON is used as the canonical format because it preserves both text and timing. TXT, SRT or VTT can be generated later from the structured result.

---

## 9. Handling Different Audio Formats

The pipeline uses FFprobe and FFmpeg as a common media decoding and normalization layer instead of implementing separate decoders for every extension.

### Processing sequence

1. Perform an initial extension check.
2. Inspect the actual media with FFprobe.
3. Confirm that an audio stream exists.
4. Read container, codec, duration, sample rate, channels and size.
5. Extract the first audio stream with FFmpeg.
6. Remove video when present.
7. Convert the audio to mono.
8. Resample to 16 kHz.
9. Encode as 16-bit PCM WAV.
10. Pass the normalized audio to WhisperX.

### FFprobe inspection

The implementation is conceptually equivalent to:

```powershell
ffprobe -v error `
  -select_streams a:0 `
  -show_entries stream=codec_name,sample_rate,channels,duration `
  -show_entries format=format_name,duration,size `
  -of json input_file
```

The input is rejected if:

- FFprobe cannot open it
- no audio stream exists
- metadata cannot be parsed
- the installed FFmpeg build cannot decode it.

### FFmpeg normalization

The implementation is equivalent to-

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

Options:

- `-map 0:a:0`: select the first audio stream.
- `-vn`: exclude video.
- `-ac 1`: convert to mono.
- `-ar 16000`: resample to 16 kHz.
- `-c:a pcm_s16le`: create 16-bit PCM audio.

The normalized file exists only in a temporary directory and is removed after success or failure.

### Common recognized extensions

```text
.wav .mp3 .flac .m4a .aac .ogg .oga .opus
.wma .amr .aif .aiff .webm .mp4 .mov .mkv
.avi .wmv .flv .mpeg .mpg .3gp .m4v
```

Actual compatibility is correctly described as **formats and codecs supported by the installed FFmpeg build**. Unknown extensions are still probed which allows decodable media to work without relying solely on an allowlist.

### Why explicit normalization

Although direct decoding can avoid an intermediate WAV, explicit normalization was selected because it provides -

- predictable model input
- early media validation
- clear decoding errors
- audio extraction from video
- easier debugging
- consistent behavior across formats

---

## 10. Handling Long Audio Files

### Implemented local approach

The local script normalizes the complete recording once and passes it to WhisperX. WhisperX uses VAD to identify speech active regions and Faster-Whisper processes the speech in batches.

```text
Long recording
    -> FFmpeg normalization
    -> WhisperX VAD
    -> speech-aware regions
    -> batched transcription
    -> ordered segments on the original timeline
```

VAD-based processing was selected instead of manually creating fixed 30-second files because fixed boundaries can cut through words, sentences, or speaker turns.

The implemented approach avoids custom logic for -

- creating temporary chunk files
- overlapping adjacent chunks
- removing duplicated boundary text
- converting local chunk timestamps to global timestamps
- merging many partial results

### Verified test

The implementation was tested with an MP4 recording of approximately -

```text
863 seconds
approximately 14 minutes and 23 seconds
```

The generated JSON contained ordered segment timestamps through approximately 862 seconds confirming that the complete recording was processed.

### Production extension for multi-hour audio

For multi-hour recordings, the recommended production design is:

1. Store the original media.
2. Create an asynchronous transcription job.
3. Generate a VAD-based chunk manifest.
4. Persist each chunk's original start and end offsets.
5. Process chunks through controlled workers.
6. Save partial chunk results.
7. Add each chunk's source offset to its local timestamps.
8. Sort all segments by global start time.
9. Remove duplicates if overlap was used.
10. Write the final transcript atomically.

Chunk-level checkpointing means that a failed chunk can be retried without retranscribing completed chunks.

---

## 11. Failure Handling in the Implemented Script

The script validates inexpensive prerequisites before expensive inference -

- source path exists
- FFprobe and FFmpeg are available
- media contains a decodable audio stream
- FFmpeg exits successfully
- normalized output exists and is non-empty.

Selected WhisperX failures represented by `RuntimeError` or `OSError` are retried with short bounded exponential delays.

Default behavior -

```text
Initial attempt
Retry after approximately 1 second
Retry after approximately 2 seconds
Stop and report the final failure
```

Invalid media and FFmpeg validation failures are not blindly retried because repeatedly processing the same invalid input is unlikely to succeed.

The retry path was exercised during Windows testing: the first model-cache operation encountered a symlink privilege error, and the next attempt completed successfully.

---

## 12. Canonical JSON Output

The result is written atomically - 

1. Write `<output>.tmp`.
2. Complete and validate serialization.
3. Replace the final output path.

This reduces the chance of leaving a partially written JSON file.

---

## 13. Verified Local Execution

### Input

```text
2.mp4
```

### Command

```powershell
python transcribe.py "2.mp4" `
  --model small `
  --device cpu `
  --compute-type int8 `
  --batch-size 2
```

### Observed result

- WhisperX `small` model loaded on CPU.
- Compute type was `int8`.
- English was detected automatically.
- FFprobe identified AAC stereo audio at 44.1 kHz.
- Source duration was approximately 863 seconds.
- Output file was `2.transcript.json`.
- Output contained ordered segment-level timestamps.
- The final segment extended to approximately 862 seconds.
- Model-reported processing time was approximately 144 seconds, excluding part of the first model download setup.

---

## 14. Windows Setup

### Prerequisites

- Python 3.10 or 3.11.
- FFmpeg and FFprobe installed and available on `PATH`.
- Internet access for the initial model download.

Verify FFmpeg:

```powershell
ffmpeg -version
ffprobe -version
```

Create a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Using Conda:

```powershell
conda activate volga
pip install -r requirements.txt
```

Run locally:

```powershell
python transcribe.py "2.mp4" --model small --device cpu --compute-type int8 --batch-size 2
```

---

## 15. Engineering Trade-offs

### WhisperX versus Faster-Whisper directly

Faster-Whisper alone can return segment timestamps with fewer dependencies. WhisperX was retained because it matches the selected stack and provides a future upgrade path to forced word alignment and speaker diarization. Those additional stages remain disabled.

### Explicit normalization versus direct decoding

Direct decoding can avoid a temporary WAV. Explicit FFmpeg normalization gives predictable model input, clearer validation failures and consistent extraction from video containers.

### CLI versus API

The CLI is the primary implemented interface because it is simple to run and review. The optional FastAPI mode demonstrates upload handling without introducing production infrastructure.

### Built-in long-form processing versus explicit chunk files

WhisperX VAD and batching are sufficient for the local assessment. Explicit chunk manifests and checkpointing become valuable when distributed processing, durable progress or chunk-level recovery is required.

### Model size

The `small` model gives a practical CPU balance between accuracy, memory use, and processing speed. Larger models can improve recognition of difficult speech or technical terms but require more memory and time.

---

# Part 2: Production System Design

## 16. Recommended Production Architecture

```text
Client
  |
  | create upload session / upload media
  v
FastAPI API layer
  - authentication and authorization
  - request validation
  - quota and rate-limit checks
  - job creation
  |
  v
Private object storage
  - original media
  - temporary normalized audio
  - chunk results
  - canonical transcript JSON
  |
  v
Durable queue
  - RabbitMQ, Redis, SQS, or equivalent
  |
  v
Controlled CPU/GPU worker pool
  - FFprobe validation
  - FFmpeg normalization
  - WhisperX transcription
  - checkpointing and retries
  |
  +-----------------------------+
  |                             |
  v                             v
PostgreSQL                  Object storage
job metadata                transcript artifacts
```

The key production decision is to separate upload handling from model inference. Uploading is primarily I/O-bound; transcription is CPU/GPU-intensive and must be concurrency-limited.

---

## 17. Handling Concurrent Uploads

### Separate upload and inference concurrency

FastAPI can accept multiple I/O-bound uploads but the service must not start one unrestricted WhisperX inference for every request.

Recommended flow:

1. Authenticate the client.
2. Create an upload or job ID.
3. Enforce size, duration, rate and storage quotas.
4. Stream media to object storage.
5. Calculate a checksum while uploading.
6. Validate the completed object with FFprobe.
7. Create the job record.
8. Publish only the job ID and storage key to a durable queue.
9. Return `202 Accepted`.

Queue message example:

```json
{
  "job_id": "tr_01JABC",
  "audio_object_key": "audio/tenant-42/tr_01JABC/original.m4a",
  "language": "en",
  "model_profile": "standard"
}
```

Audio bytes should not be placed directly in Redis, RabbitMQ, or the queue message.

### Direct-to-object-storage uploads

For large media, use a short-lived presigned or SAS URL:

1. Client requests an upload session.
2. API returns a short-lived upload URL.
3. Client uploads directly to object storage.
4. Client calls an upload-completion endpoint.
5. API validates the object and creates the transcription job.

This prevents large files from consuming application-server bandwidth and supports resumable or multipart uploads.

### Worker concurrency

A starting policy might be:

```text
API upload concurrency:       many I/O-bound requests
CPU workers:                  1-2 per machine initially
GPU workers:                  1 per GPU initially
Worker prefetch:              low for long tasks
Additional jobs:              remain queued
```

Actual limits should be determined through load testing based on model size, batch size, audio duration, CPU, RAM, GPU, and VRAM.

### Backpressure

Apply:

- maximum file size
- maximum duration
- concurrent-upload limit per user
- pending-job limit per tenant
- rate limits
- storage quotas
- maximum queue depth
- service-capacity checks.

When user-specific limits are exceeded:

```http
429 Too Many Requests
Retry-After: 60
```

When the service has no temporary capacity:

```http
503 Service Unavailable
Retry-After: 120
```

### Idempotency

Support:

```http
Idempotency-Key: <client-generated-key>
```

Enforce uniqueness on `tenant_id + idempotency_key`. A repeated request should return the existing job rather than create duplicate media and transcription work.

---

## 18. Storing Audio and Transcripts

### Storage separation

Use private object storage for large artifacts and PostgreSQL for operational metadata.

#### Object storage

Store:

- original media
- temporary normalized audio when required
- chunk-level partial results
- canonical versioned transcript JSON
- derived TXT, SRT, and VTT artifacts
- limited diagnostics for failed jobs subject to policy.

Suitable services include S3, Azure Blob Storage, Google Cloud Storage or an S3-compatible platform.

#### PostgreSQL

Store:

- job ID and status
- tenant and owner
- original filename
- object keys
- file size and checksum
- media duration and format
- detected language
- model and pipeline versions
- progress and chunk counts
- retry attempts
- error code and message
- creation, start, completion, and expiry timestamps
- optional searchable transcript text or preview.

Redis should be used for queueing, rate limiting, locks or temporary progress caching not as the permanent system of record.

### Object-key design

Do not use the untrusted original filename as the physical object key.

```text
audio/{tenant_id}/{job_id}/original.m4a
temporary/{tenant_id}/{job_id}/normalized.wav
chunks/{tenant_id}/{job_id}/000001.json
transcripts/{tenant_id}/{job_id}/v1/transcript.json
transcripts/{tenant_id}/{job_id}/v1/transcript.srt
```

Store the original filename only as metadata.

### Canonical transcript

The canonical transcript should be versioned JSON containing:

- schema version
- transcript version
- job ID
- source-media metadata
- checksum
- detected language
- complete text
- timestamped segments
- model and pipeline versions
- VAD and alignment configuration
- processing timestamps.

TXT, SRT and VTT are derived formats and can be generated from this canonical JSON.

### Retention

An example configurable lifecycle:

```text
Normalized temporary audio:     delete after success or within 24 hours
Failed temporary artifacts:     retain up to 7 days
Original media:                 retain 30 days
Transcript artifacts:           retain 90 days or according to contract
Job metadata:                   retain according to audit requirements
```

Retention must be adjusted for legal, privacy, contractual, and tenant-specific requirements.

### Security

- TLS in transit.
- Encryption at rest.
- Private buckets or containers.
- Tenant-scoped authorization.
- Least-privilege worker identities.
- Short-lived signed download URLs.
- Audit logging for access and deletion.
- Regional storage where required.
- Checksums for integrity.
- No raw audio or transcript content in routine application logs.

---

## 19. Retry and Failure Recovery

### Classify failures before retrying

#### Transient failures: retry

Examples:

- temporary storage timeout
- database connection interruption
- broker or network failure
- temporary service unavailability
- worker restart.

Use capped exponential backoff with jitter:

```text
Attempt 1: immediately
Attempt 2: approximately 10 seconds
Attempt 3: approximately 30 seconds
Attempt 4: approximately 90 seconds
Attempt 5: approximately 5 minutes
Then: RETRY_EXHAUSTED
```

#### Resource failures: retry with a safer profile

Examples:

- CUDA or RAM out-of-memory
- batch size too large
- audio chunk too long
- temporary disk pressure.

Fallback example:

```text
GPU batch 16
    -> GPU batch 8
    -> GPU batch 2
    -> smaller chunks
    -> CPU fallback or manual review
```

Retrying the exact same resource configuration is unlikely to solve the problem.

#### Permanent failures: do not retry automatically

Examples:

- corrupt or encrypted media
- unsupported codec
- no audio stream
- missing source object
- invalid parameters
- file-size or duration violation
- authorization failure.

Return a stable error contract:

```json
{
  "status": "failed",
  "error": {
    "code": "NO_AUDIO_STREAM",
    "message": "The uploaded media does not contain a decodable audio stream.",
    "retryable": false
  }
}
```

### Idempotent workers

The queue should be treated as at-least-once delivery. A worker must:

1. Atomically claim an eligible job.
2. Return the existing result if already completed.
3. Use deterministic output keys.
4. Write results to a temporary key.
5. Validate the result.
6. Publish the final result atomically.
7. Update the database to `COMPLETED` only after the final result exists.

### Worker crash recovery

For idempotent tasks, use late acknowledgment carefully so unfinished work can be redelivered after a worker exits.

Safeguards:

- maximum attempt count
- low prefetch for long tasks
- explicit I/O timeouts
- worker heartbeat or lease
- soft and hard processing limits
- safer fallback profiles
- dead-letter handling.

### Long-audio checkpoint recovery

Maintain per-chunk state:

```text
PENDING
PROCESSING
COMPLETED
RETRY_SCHEDULED
FAILED
```

Persist every completed chunk's JSON. After restart, resume only failed or pending chunks.

### Stuck-job recovery

Store:

```text
worker_id
heartbeat_at
lease_expires_at
```

A reconciliation process can requeue a job when it remains `PROCESSING` after its worker lease has expired.

### Dead-letter and manual review

After the retry budget is exhausted, move the job to `RETRY_EXHAUSTED`. Preserve the source object, failure classification, attempt history, processing profile, and latest completed checkpoint so an authorized operator can retry safely.

---

## 20. REST API Design

Use a versioned asynchronous REST API.

### Recommended endpoints

```text
POST   /api/v1/uploads
POST   /api/v1/uploads/{upload_id}/complete
POST   /api/v1/transcriptions
GET    /api/v1/transcriptions/{job_id}
GET    /api/v1/transcriptions/{job_id}/result
POST   /api/v1/transcriptions/{job_id}/retry
POST   /api/v1/transcriptions/{job_id}/cancel
DELETE /api/v1/transcriptions/{job_id}
GET    /health/live
GET    /health/ready
```

### Create a transcription with multipart upload

```http
POST /api/v1/transcriptions
Authorization: Bearer <token>
Idempotency-Key: <unique-key>
Content-Type: multipart/form-data
```

Possible fields:

```text
file
language
model_profile
timestamps=segment
output_formats=json,srt
callback_url
```

### Create a transcription from a completed direct upload

```http
POST /api/v1/transcriptions
Authorization: Bearer <token>
Idempotency-Key: <unique-key>
Content-Type: application/json
```

```json
{
  "upload_id": "up_01JABC",
  "language": "en",
  "timestamps": "segment",
  "output_formats": ["json", "srt"]
}
```

### Accepted response

```http
HTTP/1.1 202 Accepted
Location: /api/v1/transcriptions/tr_01JABC
Retry-After: 5
```

```json
{
  "job_id": "tr_01JABC",
  "status": "queued",
  "status_url": "/api/v1/transcriptions/tr_01JABC",
  "result_url": "/api/v1/transcriptions/tr_01JABC/result",
  "created_at": "2026-11-01T12:00:00Z"
}
```

### Job states

```text
UPLOADING
VALIDATING
QUEUED
PROCESSING
RETRY_SCHEDULED
COMPLETED
FAILED
RETRY_EXHAUSTED
CANCELLATION_REQUESTED
CANCELLED
DELETING
DELETED
```

### Status response

```json
{
  "job_id": "tr_01JABC",
  "status": "processing",
  "progress": {
    "percent": 42.5,
    "processed_seconds": 263.0,
    "total_seconds": 618.4,
    "completed_chunks": 9,
    "total_chunks": 21
  },
  "attempt_count": 1,
  "error": null
}
```

Clients should respect `Retry-After` or use polling backoff rather than polling continuously.

### Result response

```json
{
  "job_id": "tr_01JABC",
  "status": "completed",
  "language": "en",
  "duration_seconds": 618.4,
  "text": "Complete transcript...",
  "segments": [
    {
      "id": 0,
      "start": 0.48,
      "end": 3.62,
      "text": "Good morning everyone."
    }
  ],
  "artifacts": {
    "json": "/api/v1/transcriptions/tr_01JABC/result?format=json",
    "srt": "/api/v1/transcriptions/tr_01JABC/result?format=srt",
    "vtt": "/api/v1/transcriptions/tr_01JABC/result?format=vtt"
  }
}
```

### Optional webhooks

Support events such as:

```text
transcription.completed
transcription.failed
transcription.cancelled
```

Webhook delivery should include an event ID, timestamp, HMAC signature, retry policy, and duplicate-event tolerance.

### HTTP status codes

- `200 OK`: status or result returned.
- `201 Created`: upload session created.
- `202 Accepted`: transcription queued.
- `400 Bad Request`: invalid option combination.
- `401 Unauthorized`: missing or invalid authentication.
- `403 Forbidden`: insufficient permission.
- `404 Not Found`: job does not exist or is not visible.
- `409 Conflict`: invalid job-state transition.
- `413 Content Too Large`: upload exceeds the limit.
- `415 Unsupported Media Type`: media cannot be decoded.
- `422 Unprocessable Content`: request validation failed.
- `429 Too Many Requests`: user or tenant limit exceeded.
- `503 Service Unavailable`: temporary capacity unavailable.

### Error contract

```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA",
    "message": "The uploaded file does not contain a decodable audio stream.",
    "retryable": false,
    "request_id": "req_01JABC"
  }
}
```

Do not expose stack traces, local paths, credentials, queue internals, or database errors.

### Authentication and authorization

Use OAuth 2.0 or OpenID Connect bearer tokens. Every upload and transcription job must be scoped to a tenant and owner. Authorization must be enforced for upload, status, result, retry, cancellation, download, and deletion operations.

### Health and observability

`/health/live` should confirm that the API process is alive. `/health/ready` should confirm that required dependencies such as the database, broker, and storage are available.

Monitor:

- upload throughput and failures
- queue depth and oldest-job age
- queued and processing latency
- real-time transcription factor
- retry count by error category
- CPU, RAM, GPU, and VRAM utilization
- temporary-disk and object-storage usage
- stuck jobs; and
- webhook delivery success.

Use consistent `request_id`, `job_id`, `tenant_id` and `trace_id` values across API logs, queue messages, worker logs, and storage operations.

---

## 21. Final Design Summary

### Implemented assessment pipeline

```text
Local file or optional FastAPI multipart upload
    -> FFprobe validation
    -> FFmpeg extraction and 16 kHz mono normalization
    -> WhisperX/Faster-Whisper transcription with VAD
    -> segment-level timestamps
    -> atomic JSON output
    -> automatic temporary-file cleanup
```

### Recommended production system

```text
Authenticated API
    -> direct or multipart object-storage upload
    -> persisted job record
    -> durable queue
    -> bounded CPU/GPU worker pool
    -> FFprobe and FFmpeg preprocessing
    -> WhisperX transcription
    -> chunk checkpoints and classified retries
    -> canonical transcript JSON
    -> status, result, webhook, retry, and deletion APIs
```

The design cleanly separates responsibilities:

- **FastAPI** coordinates requests and job state.
- **Object storage** holds large media and transcript artifacts.
- **PostgreSQL** stores durable operational metadata.
- **A durable broker** buffers work and provides backpressure.
- **Controlled workers** perform resource-intensive inference.
- **FFprobe/FFmpeg** handle heterogeneous media.
- **WhisperX/Faster-Whisper** perform speech recognition.
- **JSON** preserves transcript text, timestamps, and processing metadata.

This keeps the assessment implementation simple and runnable while demonstrating a credible path to a secure, recoverable, and horizontally scalable real-world transcription platform.

---