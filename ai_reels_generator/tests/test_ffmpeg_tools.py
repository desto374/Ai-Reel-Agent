from unittest.mock import patch

from tools.ffmpeg_tools import (
    burn_subtitles,
    create_edit_proxy,
    cut_clip,
    estimate_chunk_count,
    extract_audio,
    prepare_transcription_audio,
    split_audio_chunks,
    to_vertical,
)


@patch("tools.ffmpeg_tools.ensure_ffmpeg", return_value="ffmpeg")
@patch("tools.ffmpeg_tools.run_cmd")
def test_extract_audio_builds_expected_command(mock_run_cmd, _mock_ffmpeg):
    result = extract_audio("input.mp4", "audio.wav")
    assert result == "audio.wav"
    mock_run_cmd.assert_called_once_with(
        ["ffmpeg", "-y", "-i", "input.mp4", "-vn", "-acodec", "pcm_s16le", "audio.wav"]
    )


@patch("tools.ffmpeg_tools.ensure_ffmpeg", return_value="ffmpeg")
@patch("tools.ffmpeg_tools.run_cmd")
def test_cut_clip_builds_expected_command(mock_run_cmd, _mock_ffmpeg):
    result = cut_clip("input.mp4", 5.0, 25.0, "clip.mp4")
    assert result == "clip.mp4"
    mock_run_cmd.assert_called_once_with(
        [
            "ffmpeg",
            "-y",
            "-i",
            "input.mp4",
            "-ss",
            "5.0",
            "-to",
            "25.0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "clip.mp4",
        ]
    )


@patch("tools.ffmpeg_tools.ensure_ffmpeg", return_value="ffmpeg")
@patch("tools.ffmpeg_tools.run_cmd")
def test_to_vertical_builds_expected_command(mock_run_cmd, _mock_ffmpeg):
    result = to_vertical("clip.mp4", "vertical.mp4")
    assert result == "vertical.mp4"
    mock_run_cmd.assert_called_once_with(
        [
            "ffmpeg",
            "-y",
            "-i",
            "clip.mp4",
            "-vf",
            "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "vertical.mp4",
        ]
    )


@patch("tools.ffmpeg_tools.ensure_ffmpeg", return_value="ffmpeg")
@patch("tools.ffmpeg_tools.run_cmd")
def test_burn_subtitles_builds_expected_command(mock_run_cmd, _mock_ffmpeg):
    result = burn_subtitles("vertical.mp4", "captions.srt", "captioned.mp4")
    assert result == "captioned.mp4"
    mock_run_cmd.assert_called_once_with(
        [
            "ffmpeg",
            "-y",
            "-i",
            "vertical.mp4",
            "-vf",
            "subtitles=captions.srt",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "captioned.mp4",
        ]
    )


@patch("tools.ffmpeg_tools.ensure_ffmpeg", return_value="ffmpeg")
@patch("tools.ffmpeg_tools.run_cmd")
def test_create_edit_proxy_builds_expected_command(mock_run_cmd, _mock_ffmpeg):
    result = create_edit_proxy("input.mov", "proxy.mp4")
    assert result == "proxy.mp4"
    mock_run_cmd.assert_called_once_with(
        [
            "ffmpeg",
            "-y",
            "-i",
            "input.mov",
            "-vf",
            "scale='min(1280,iw)':-2",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "31",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "proxy.mp4",
        ]
    )


@patch("tools.ffmpeg_tools.ensure_ffmpeg", return_value="ffmpeg")
@patch("tools.ffmpeg_tools.run_cmd")
def test_prepare_transcription_audio_builds_expected_command(mock_run_cmd, _mock_ffmpeg):
    result = prepare_transcription_audio("audio.wav", "audio.mp3")
    assert result == "audio.mp3"
    mock_run_cmd.assert_called_once_with(
        [
            "ffmpeg",
            "-y",
            "-i",
            "audio.wav",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "32k",
            "audio.mp3",
        ]
    )


@patch("tools.ffmpeg_tools.ensure_ffmpeg", return_value="ffmpeg")
@patch("tools.ffmpeg_tools.run_cmd")
def test_split_audio_chunks_builds_expected_command(mock_run_cmd, _mock_ffmpeg, tmp_path):
    result = split_audio_chunks("audio.mp3", str(tmp_path), chunk_seconds=480)
    assert result == []
    mock_run_cmd.assert_called_once_with(
        [
            "ffmpeg",
            "-y",
            "-i",
            "audio.mp3",
            "-f",
            "segment",
            "-segment_time",
            "480",
            "-reset_timestamps",
            "1",
            "-c",
            "copy",
            str(tmp_path / "chunk_%03d.mp3"),
        ]
    )


def test_estimate_chunk_count_rounds_up():
    assert estimate_chunk_count(25, 10) == 3
