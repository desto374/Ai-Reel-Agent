import pytest

from models.schemas import ClipCandidate, RenderedClip, TranscriptBundle, TranscriptSegment


def test_transcript_bundle_accepts_segments():
    bundle = TranscriptBundle(
        segments=[TranscriptSegment(start=0.0, end=10.0, text="Hello world")],
        raw_text="Hello world",
    )
    assert bundle.raw_text == "Hello world"
    assert bundle.segments[0].start == 0.0


def test_clip_candidate_score_bounds():
    with pytest.raises(Exception):
        ClipCandidate(title="Bad", start=0.0, end=5.0, score=12.0, reason="Too high")


def test_rendered_clip_defaults():
    clip = RenderedClip(
        title="Example",
        source_start=0.0,
        source_end=10.0,
        clip_path="outputs/clips/example.mp4",
    )
    assert clip.vertical_path is None
    assert clip.captioned_path is None
