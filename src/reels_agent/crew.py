from __future__ import annotations

from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task

from .tools import (
    BurnCaptionsTool,
    CutClipTool,
    ExtractAudioTool,
    GenerateCaptionsTool,
    PrepareJobTool,
    ReframeClipTool,
    RunQATool,
    SelectClipsTool,
    TranscribeAudioTool,
    UploadToDriveTool,
)


CONFIG_DIR = Path(__file__).resolve().parent / "config"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_crew() -> Crew:
    agents_config = load_yaml(CONFIG_DIR / "agents.yaml")
    tasks_config = load_yaml(CONFIG_DIR / "tasks.yaml")

    prepare_job_tool = PrepareJobTool()
    extract_audio_tool = ExtractAudioTool()
    transcribe_audio_tool = TranscribeAudioTool()
    select_clips_tool = SelectClipsTool()
    cut_clip_tool = CutClipTool()
    reframe_clip_tool = ReframeClipTool()
    generate_captions_tool = GenerateCaptionsTool()
    burn_captions_tool = BurnCaptionsTool()
    run_qa_tool = RunQATool()
    upload_to_drive_tool = UploadToDriveTool()

    intake_coordinator = Agent(
        verbose=True,
        tools=[prepare_job_tool],
        **agents_config["intake_coordinator"],
    )
    transcription_analyst = Agent(
        verbose=True,
        tools=[extract_audio_tool, transcribe_audio_tool],
        **agents_config["transcription_analyst"],
    )
    clip_strategist = Agent(
        verbose=True,
        tools=[select_clips_tool],
        **agents_config["clip_strategist"],
    )
    reframing_director = Agent(
        verbose=True,
        tools=[cut_clip_tool, reframe_clip_tool, generate_captions_tool, burn_captions_tool],
        **agents_config["reframing_director"],
    )
    qa_delivery_manager = Agent(
        verbose=True,
        tools=[run_qa_tool, upload_to_drive_tool],
        **agents_config["qa_delivery_manager"],
    )

    intake_task = Task(agent=intake_coordinator, **tasks_config["intake_task"])
    transcription_task = Task(agent=transcription_analyst, **tasks_config["transcription_task"])
    clip_selection_task = Task(agent=clip_strategist, **tasks_config["clip_selection_task"])
    reframing_task = Task(agent=reframing_director, **tasks_config["reframing_task"])
    qa_delivery_task = Task(agent=qa_delivery_manager, **tasks_config["qa_delivery_task"])

    return Crew(
        agents=[
            intake_coordinator,
            transcription_analyst,
            clip_strategist,
            reframing_director,
            qa_delivery_manager,
        ],
        tasks=[
            intake_task,
            transcription_task,
            clip_selection_task,
            reframing_task,
            qa_delivery_task,
        ],
        process=Process.sequential,
        verbose=True,
    )
