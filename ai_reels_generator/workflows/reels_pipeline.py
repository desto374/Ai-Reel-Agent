from __future__ import annotations

from crewai_bootstrap import bootstrap_crewai_environment

bootstrap_crewai_environment()

from crewai import Crew, Process

from agents.caption_agent import build_caption_agent
from agents.clip_selector_agent import build_clip_selector_agent
from agents.export_agent import build_export_agent
from agents.transcription_agent import build_transcription_agent
from agents.video_editor_agent import build_video_editor_agent
from tasks.caption_task import build_caption_task
from tasks.clip_selection_task import build_clip_selection_task
from tasks.edit_task import build_edit_task
from tasks.export_task import build_export_task
from tasks.transcription_task import build_transcription_task


def build_reels_pipeline() -> Crew:
    transcription_agent = build_transcription_agent()
    clip_selector_agent = build_clip_selector_agent()
    video_editor_agent = build_video_editor_agent()
    caption_agent = build_caption_agent()
    export_agent = build_export_agent()

    transcription_task = build_transcription_task()
    transcription_task.agent = transcription_agent
    transcription_task.description = (
        transcription_task.description
        + "\nUse the provided `transcript_json` and explain the strongest hooks, topic shifts, and emotional peaks."
    )

    clip_selection_task = build_clip_selection_task()
    clip_selection_task.agent = clip_selector_agent
    clip_selection_task.context = [transcription_task]
    clip_selection_task.description = (
        clip_selection_task.description
        + "\nUse the transcript data provided in `transcript_json`."
        + "\nReturn a top-level JSON object with a `clips` array."
    )

    edit_task = build_edit_task()
    edit_task.agent = video_editor_agent
    edit_task.context = [clip_selection_task]
    edit_task.description = (
        edit_task.description
        + "\nSummarize the editing plan for the selected clips using the chosen timestamps."
    )

    caption_task = build_caption_task()
    caption_task.agent = caption_agent
    caption_task.context = [edit_task]
    caption_task.description = (
        caption_task.description
        + "\nSummarize subtitle readability guidelines for the selected clips."
    )

    export_task = build_export_task()
    export_task.agent = export_agent
    export_task.context = [caption_task]
    export_task.description = (
        export_task.description
        + "\nSummarize the expected manifest and delivery outputs for the selected clips."
    )

    crew = Crew(
        agents=[
            transcription_agent,
            clip_selector_agent,
            video_editor_agent,
            caption_agent,
            export_agent,
        ],
        tasks=[
            transcription_task,
            clip_selection_task,
            edit_task,
            caption_task,
            export_task,
        ],
        process=Process.sequential,
        verbose=True,
    )
    return crew
