# WhisperX Transcription Assessment

<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)

## 2. Implemented Technology Stack

- **Python 3.10/3.11** for the application.
- **FastAPI** for the optional multipart upload demonstration.
<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)

## 4. Repository Contents

```text
.
├── transcribe.py
├── requirements.txt
└── README.md
```

<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)

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

<<<<<<< HEAD
The options mean:

- `-map 0:a:0`: select the first audio stream;
- `-vn`: exclude video;
- `-ac 1`: convert to mono;
- `-ar 16000`: resample to 16 kHz; and
- `-c:a pcm_s16le`: create 16-bit PCM audio.

The normalized WAV exists only inside a temporary directory and is automatically removed after success or failure.

### Supported formats

The script recognizes common extensions including:
=======
Options:

- `-map 0:a:0`: select the first audio stream.
- `-vn`: exclude video.
- `-ac 1`: convert to mono.
- `-ar 16000`: resample to 16 kHz.
- `-c:a pcm_s16le`: create 16-bit PCM audio.

The normalized file exists only in a temporary directory and is removed after success or failure.

### Common recognized extensions
>>>>>>> 7d19e13 (Update readme)

```text
.wav .mp3 .flac .m4a .aac .ogg .oga .opus
.wma .amr .aif .aiff .webm .mp4 .mov .mkv
.avi .wmv .flv .mpeg .mpg .3gp .m4v
```

<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)

```text
2.mp4
```

<<<<<<< HEAD
Command:
=======
### Command
>>>>>>> 7d19e13 (Update readme)

```powershell
python transcribe.py "2.mp4" `
  --model small `
  --device cpu `
  --compute-type int8 `
  --batch-size 2
```

<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)

### Prerequisites

- Python 3.10 or 3.11.
- FFmpeg and FFprobe installed and available on `PATH`.
<<<<<<< HEAD
- Internet access for the first model download.
=======
- Internet access for the initial model download.
>>>>>>> 7d19e13 (Update readme)

Verify FFmpeg:

```powershell
ffmpeg -version
ffprobe -version
```

<<<<<<< HEAD
Create and activate an environment:
=======
Create a virtual environment:
>>>>>>> 7d19e13 (Update readme)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

<<<<<<< HEAD
If using Conda:
=======
Using Conda:
>>>>>>> 7d19e13 (Update readme)

```powershell
conda activate volga
pip install -r requirements.txt
```

<<<<<<< HEAD
=======
Run locally:

```powershell
python transcribe.py "2.mp4" --model small --device cpu --compute-type int8 --batch-size 2
```

---

>>>>>>> 7d19e13 (Update readme)
## 15. Engineering Trade-offs

### WhisperX versus Faster-Whisper directly

<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)
```

#### Resource failures: retry with a safer profile

<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)

```http
POST /api/v1/transcriptions
Authorization: Bearer <token>
Idempotency-Key: <unique-key>
Content-Type: multipart/form-data
```

<<<<<<< HEAD
Response:

```http
HTTP/1.1 202 Accepted
Location: /api/v1/transcriptions/{job_id}
=======
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
>>>>>>> 7d19e13 (Update readme)
Retry-After: 5
```

```json
{
<<<<<<< HEAD
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

=======
  "job_id": "tr_01JABC",
  "status": "queued",
  "status_url": "/api/v1/transcriptions/tr_01JABC",
  "result_url": "/api/v1/transcriptions/tr_01JABC/result",
  "created_at": "2026-11-01T12:00:00Z"
}
```

>>>>>>> 7d19e13 (Update readme)
### Job states

```text
UPLOADING
<<<<<<< HEAD
=======
VALIDATING
>>>>>>> 7d19e13 (Update readme)
QUEUED
PROCESSING
RETRY_SCHEDULED
COMPLETED
FAILED
RETRY_EXHAUSTED
<<<<<<< HEAD
CANCELLED
=======
CANCELLATION_REQUESTED
CANCELLED
DELETING
>>>>>>> 7d19e13 (Update readme)
DELETED
```

### Status response

```json
{
<<<<<<< HEAD
  "job_id": "8595818c-cc7f-404c-a776-a504c625e231",
  "status": "processing",
  "progress_percent": 42.5,
  "processed_duration_seconds": 263.0,
  "total_duration_seconds": 618.4,
=======
  "job_id": "tr_01JABC",
  "status": "processing",
  "progress": {
    "percent": 42.5,
    "processed_seconds": 263.0,
    "total_seconds": 618.4,
    "completed_chunks": 9,
    "total_chunks": 21
  },
>>>>>>> 7d19e13 (Update readme)
  "attempt_count": 1,
  "error": null
}
```

<<<<<<< HEAD
### Error structure
=======
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
>>>>>>> 7d19e13 (Update readme)

```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA",
    "message": "The uploaded file does not contain a decodable audio stream.",
<<<<<<< HEAD
    "request_id": "req_923cf4a7"
=======
    "retryable": false,
    "request_id": "req_01JABC"
>>>>>>> 7d19e13 (Update readme)
  }
}
```

<<<<<<< HEAD
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
=======
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
>>>>>>> 7d19e13 (Update readme)
    -> WhisperX/Faster-Whisper transcription with VAD
    -> segment-level timestamps
    -> atomic JSON output
    -> automatic temporary-file cleanup
```

<<<<<<< HEAD
This design cleanly separates media handling from speech recognition. FFmpeg is responsible for heterogeneous media inputs WhisperX is responsible for transcription and the Python application is responsible for validation, retries, result shaping and cleanup.

=======
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
>>>>>>> 7d19e13 (Update readme)
