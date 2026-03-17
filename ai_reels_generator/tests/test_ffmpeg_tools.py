from unittest.mock import patch

from tools.ffmpeg_tools import burn_subtitles, cut_clip, extract_audio, to_vertical


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
            "-c:a",
            "aac",
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
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
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
            "-c:a",
            "aac",
            "captioned.mp4",
        ]
    )
