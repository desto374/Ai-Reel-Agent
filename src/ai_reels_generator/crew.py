from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2] / "ai_reels_generator"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


try:
    from crewai import Crew, Process
    from crewai.project import CrewBase, agent, crew, task
except ImportError:  # Keeps local validation importable before dependencies are installed.
    class _FallbackProcess:
        sequential = "sequential"

    def CrewBase(cls):
        return cls

    def agent(func):
        return func

    def task(func):
        return func

    def crew(func):
        return func

    class Crew:  # type: ignore[override]
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def kickoff(self, inputs: dict | None = None):
            return {"status": "fallback", "inputs": inputs or {}}

    Process = _FallbackProcess()


@CrewBase
class AiReelsGeneratorCrew:
    """Deployment-compatible CrewAI entrypoint."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def transcription_agent(self):
        from agents.transcription_agent import build_transcription_agent

        return build_transcription_agent()

    @agent
    def clip_selector_agent(self):
        from agents.clip_selector_agent import build_clip_selector_agent

        return build_clip_selector_agent()

    @agent
    def video_editor_agent(self):
        from agents.video_editor_agent import build_video_editor_agent

        return build_video_editor_agent()

    @agent
    def caption_agent(self):
        from agents.caption_agent import build_caption_agent

        return build_caption_agent()

    @agent
    def export_agent(self):
        from agents.export_agent import build_export_agent

        return build_export_agent()

    @task
    def transcription_task(self):
        from tasks.transcription_task import build_transcription_task

        task_obj = build_transcription_task()
        task_obj.agent = self.transcription_agent()
        task_obj.description = (
            "Use the source video at {video_path}. Extract audio, create a transcript, "
            "and analyze hooks and topic shifts. Supported formats are mp4 and mov. "
            "If {source_type} is 'url', treat {video_path} as a remote file URL. "
            "If {source_type} is 'local', treat {video_path} as a file path already "
            "available to the runtime."
        )
        return task_obj

    @task
    def clip_selection_task(self):
        from tasks.clip_selection_task import build_clip_selection_task

        task_obj = build_clip_selection_task()
        task_obj.agent = self.clip_selector_agent()
        task_obj.context = [self.transcription_task()]
        task_obj.description = (
            "Select {output_count} high-quality short-form clip candidates from the "
            "transcript. Each clip should usually be between {clip_length_min} and "
            "{clip_length_max} seconds."
        )
        return task_obj

    @task
    def edit_task(self):
        from tasks.edit_task import build_edit_task

        task_obj = build_edit_task()
        task_obj.agent = self.video_editor_agent()
        task_obj.context = [self.clip_selection_task()]
        task_obj.description = (
            "Plan the cut and vertical conversion steps for selected clips from "
            "{video_path}. The output format should be 9:16 vertical reels."
        )
        return task_obj

    @task
    def caption_task(self):
        from tasks.caption_task import build_caption_task

        task_obj = build_caption_task()
        task_obj.agent = self.caption_agent()
        task_obj.context = [self.edit_task()]
        task_obj.description = (
            "Plan subtitle generation and caption burn-in for each clip. "
            "If {brand_profile} is provided, use it as the visual styling direction."
        )
        return task_obj

    @task
    def export_task(self):
        from tasks.export_task import build_export_task

        task_obj = build_export_task()
        task_obj.agent = self.export_agent()
        task_obj.context = [self.caption_task()]
        task_obj.description = (
            "Plan manifest generation and delivery output handling. "
            "If {upload_to_drive} is true, prepare Google Drive delivery."
        )
        return task_obj

    @crew
    def crew(self):
        return Crew(
            agents=[
                self.transcription_agent(),
                self.clip_selector_agent(),
                self.video_editor_agent(),
                self.caption_agent(),
                self.export_agent(),
            ],
            tasks=[
                self.transcription_task(),
                self.clip_selection_task(),
                self.edit_task(),
                self.caption_task(),
                self.export_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )


def kickoff(inputs: dict | None = None):
    return AiReelsGeneratorCrew().crew().kickoff(inputs=inputs or {})
