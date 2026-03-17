import { renderLiveJobs } from "./renderers.js";
import { setStatus } from "./ui.js";

function overallStatusMessage(responses) {
  const finished = responses.filter((job) => job.status === "completed" || job.status === "failed").length;
  const failed = responses.filter((job) => job.status === "failed").length;
  const completed = responses.filter((job) => job.status === "completed").length;

  if (finished === responses.length) {
    if (failed && completed) {
      return "Finished with partial failures. Download completed outputs below.";
    }
    if (failed) {
      return "All jobs failed.";
    }
    return "All jobs finished. Downloads are ready.";
  }

  if (responses.some((job) => job.stage === "exporting results")) {
    return "Finalizing exports and preparing downloads…";
  }

  return "Processing uploads through the CrewAI backend…";
}

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
    overallStatusMessage(responses),
    averageProgress
  );

  if (finished !== responses.length) {
    setTimeout(() => pollJobs(state, elements), 1500);
  } else {
    elements.submitButton.disabled = false;
  }
}
