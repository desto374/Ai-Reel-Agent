from __future__ import annotations

import json
import re
from pathlib import Path

from openai import OpenAI

from config.prompts import CLIP_SELECTOR_PROMPT
from config.settings import Settings
from models.schemas import ClipCandidate, ClipCandidateList, PipelineRunResult, RenderedClip, TranscriptBundle, TranscriptSegment
from tools.ffmpeg_tools import burn_subtitles, cut_clip, extract_audio, to_vertical
from tools.storage_tools import export_to_google_drive, save_manifest
from tools.subtitle_tools import write_srt
from tools.utils import ensure_dir, write_json
from tools.whisper_tools import transcribe_audio
from workflows.reels_pipeline import build_reels_pipeline


ALLOWED_EXTENSIONS = {".mp4", ".mov"}


def is_allowed_video(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def save_uploaded_video(file_storage, uploads_dir: Path) -> Path:
    filename = Path(file_storage.filename or "").name
    if not filename or not is_allowed_video(filename):
        raise ValueError("Only .mp4 and .mov uploads are supported.")
    ensure_dir(uploads_dir)
    destination = uploads_dir / filename
    file_storage.save(destination)
    return destination


def run_pipeline(
    video_path: str | Path,
    settings: Settings,
    output_count: int = 5,
    clip_length_min: int = 20,
    clip_length_max: int = 60,
    upload_to_drive: bool = True,
) -> PipelineRunResult:
    source_video = Path(video_path).resolve()
    if not source_video.exists():
        raise FileNotFoundError(f"Source video not found: {source_video}")
    if not is_allowed_video(source_video.name):
        raise ValueError("Source video must be an .mp4 or .mov file.")

    settings.ensure_directories()
    stem = slugify(source_video.stem)
    audio_path = settings.transcripts_dir / f"{stem}.wav"
    transcript_json_path = settings.transcripts_dir / f"{stem}.json"

    extract_audio(str(source_video), str(audio_path))
    transcript_bundle = transcribe_audio(str(audio_path))
    write_json(transcript_json_path, transcript_bundle.model_dump())

    clip_candidates = select_clip_candidates_with_crewai(
        transcript_bundle=transcript_bundle,
        output_count=output_count,
        clip_length_min=clip_length_min,
        clip_length_max=clip_length_max,
        openai_api_key=settings.openai_api_key,
    )

    rendered_clips: list[RenderedClip] = []
    for index, candidate in enumerate(clip_candidates, start=1):
        clip_stem = f"{stem}_{index:02d}_{slugify(candidate.title)[:40]}"
        raw_clip_path = settings.clips_dir / f"{clip_stem}.mp4"
        vertical_clip_path = settings.vertical_dir / f"{clip_stem}_vertical.mp4"
        srt_path = settings.captions_dir / f"{clip_stem}.srt"
        captioned_path = settings.captions_dir / f"{clip_stem}_captioned.mp4"

        cut_clip(str(source_video), candidate.start, candidate.end, str(raw_clip_path))
        to_vertical(str(raw_clip_path), str(vertical_clip_path))

        clip_transcript = clip_transcript_bundle(transcript_bundle, candidate.start, candidate.end)
        write_srt(clip_transcript, str(srt_path))
        burn_subtitles(str(vertical_clip_path), str(srt_path), str(captioned_path))

        rendered = RenderedClip(
            title=candidate.title,
            source_start=candidate.start,
            source_end=candidate.end,
            clip_path=str(raw_clip_path),
            vertical_path=str(vertical_clip_path),
            captioned_path=str(captioned_path),
            srt_path=str(srt_path),
        )

        if (
            upload_to_drive
            and settings.google_drive_folder_id
            and (settings.google_service_account_file or settings.google_service_account_json)
        ):
            upload_result = export_to_google_drive(
                file_path=str(captioned_path),
                folder_id=settings.google_drive_folder_id,
                service_account_file=settings.resolved_google_service_account_file(),
            )
            rendered.drive_file_id = upload_result.get("file_id")
            rendered.drive_link = upload_result.get("web_view_link") or upload_result.get("web_content_link")

        rendered_clips.append(rendered)

    manifest = {
        "source_video": str(source_video),
        "transcript_path": str(transcript_json_path),
        "clips": [clip.model_dump() for clip in rendered_clips],
    }
    manifest_path = save_manifest(str(settings.manifests_dir / f"{stem}_manifest.json"), manifest)

    return PipelineRunResult(
        source_video=str(source_video),
        transcript_path=str(transcript_json_path),
        manifest_path=manifest_path,
        clips=rendered_clips,
    )


def select_clip_candidates_with_crewai(
    transcript_bundle: TranscriptBundle,
    output_count: int,
    clip_length_min: int,
    clip_length_max: int,
    openai_api_key: str,
) -> list[ClipCandidate]:
    if not transcript_bundle.segments or not openai_api_key:
        return fallback_clip_candidates(transcript_bundle, output_count, clip_length_min, clip_length_max)

    try:
        transcript_payload = [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            }
            for segment in transcript_bundle.segments
        ]
        crew = build_reels_pipeline()
        crew.kickoff(
            inputs={
                "transcript_json": json.dumps(transcript_payload, indent=2),
                "clip_selector_prompt": CLIP_SELECTOR_PROMPT,
                "output_count": output_count,
                "clip_length_min": clip_length_min,
                "clip_length_max": clip_length_max,
            }
        )
        clip_task = crew.tasks[1]
        output_model = getattr(clip_task.output, "pydantic", None)
        if not output_model:
            raw = getattr(clip_task.output, "raw", "") or "{}"
            parsed = json.loads(raw)
            output_model = ClipCandidateList(**parsed)
        clips = output_model.clips[:output_count]
        if not clips:
            raise ValueError("Clip selector returned no clips.")
        return normalize_clip_candidates(clips, clip_length_min, clip_length_max)
    except Exception:
        return fallback_clip_candidates(transcript_bundle, output_count, clip_length_min, clip_length_max)


def fallback_clip_candidates(
    transcript_bundle: TranscriptBundle,
    output_count: int,
    clip_length_min: int,
    clip_length_max: int,
) -> list[ClipCandidate]:
    clips: list[ClipCandidate] = []
    if not transcript_bundle.segments:
        clips.append(
            ClipCandidate(
                title="Fallback Clip",
                start=0.0,
                end=float(clip_length_min),
                score=5.0,
                reason="No transcript segments were available; generated a minimal fallback clip.",
            )
        )
        return clips
    for index, segment in enumerate(transcript_bundle.segments[:output_count], start=1):
        start = segment.start
        end = max(segment.end, start + clip_length_min)
        end = min(end, start + clip_length_max)
        clips.append(
            ClipCandidate(
                title=f"Clip {index}",
                start=start,
                end=end,
                score=max(7.0, 9.5 - index * 0.4),
                reason="Fallback candidate based on transcript segment boundaries.",
            )
        )
    return clips


def normalize_clip_candidates(
    clips: list[ClipCandidate],
    clip_length_min: int,
    clip_length_max: int,
) -> list[ClipCandidate]:
    normalized: list[ClipCandidate] = []
    for clip in clips:
        duration = clip.end - clip.start
        if duration < clip_length_min:
            clip.end = clip.start + clip_length_min
        if duration > clip_length_max:
            clip.end = clip.start + clip_length_max
        normalized.append(clip)
    return normalized


def clip_transcript_bundle(bundle: TranscriptBundle, start: float, end: float) -> TranscriptBundle:
    clipped_segments: list[TranscriptSegment] = []
    for segment in bundle.segments:
        if segment.end <= start or segment.start >= end:
            continue
        clipped_segments.append(
            TranscriptSegment(
                start=max(0.0, segment.start - start),
                end=min(end - start, segment.end - start),
                text=segment.text,
            )
        )
    raw_text = " ".join(segment.text for segment in clipped_segments)
    return TranscriptBundle(segments=clipped_segments, raw_text=raw_text)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return cleaned or "clip"
