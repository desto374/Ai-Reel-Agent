import { renderLiveJobs } from "./renderers.js";
import { setStatus } from "./ui.js";

export async function pollJobs(state, elements) {
  if (!state.activeJobIds.length) {
    return;
  }

  const responses = await Promise.all(
    state.activeJobIds.map((jobId) =>
      fetch(`/api/jobs/${jobId}`).then((response) => response.json())
    )
  );

  renderLiveJobs(elements.emptyState, elements.results, responses);

  const totalProgress = responses.reduce((sum, job) => sum + (job.progress || 0), 0);
  const averageProgress = Math.round(totalProgress / responses.length);
  const finished = responses.filter((job) => job.status === "completed" || job.status === "failed").length;

  setStatus(
    elements.statusBox,
    elements.statusText,
    elements.progressBar,
    finished === responses.length
      ? "All jobs finished."
      : "Processing uploads through the CrewAI backend…",
    averageProgress
  );

  if (finished !== responses.length) {
    setTimeout(() => pollJobs(state, elements), 1500);
  } else {
    elements.submitButton.disabled = false;
  }
}
