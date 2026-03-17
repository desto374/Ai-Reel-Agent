function badgeClass(status) {
  return ["badge", status || "queued"].join(" ");
}

function artifactMarkup(clip) {
  return `
    <div class="artifact">
      <strong>${clip.title}</strong>
      <small>
        ${clip.source_start}s to ${clip.source_end}s<br>
        Captioned file: ${clip.captioned_path}<br>
        ${clip.drive_link ? `Drive: <a href="${clip.drive_link}" target="_blank" rel="noreferrer">open export</a>` : "Drive: not uploaded"}
      </small>
    </div>
  `;
}

function renderJob(job) {
  const clips = (job.result?.clips || []).map(artifactMarkup).join("");
  return `
    <article class="job-card">
      <div class="job-head">
        <div>
          <h3 class="job-title">${job.filename}</h3>
          <p class="job-subtitle">${job.result?.source_video || "Awaiting processed output"}</p>
        </div>
        <span class="${badgeClass(job.status)}">${job.status}</span>
      </div>

      <div class="job-meta">
        <div class="meta-tile">
          <span>Stage</span>
          <strong>${job.stage}</strong>
        </div>
        <div class="meta-tile">
          <span>Progress</span>
          <strong>${job.progress}%</strong>
        </div>
      </div>

      ${job.error ? `<div class="error-text">${job.error}</div>` : ""}

      ${
        job.result
          ? `
            <div class="job-meta">
              <div class="meta-tile">
                <span>Transcript</span>
                <strong>${job.result.transcript_path}</strong>
              </div>
              <div class="meta-tile">
                <span>Manifest</span>
                <strong>${job.result.manifest_path}</strong>
              </div>
            </div>
            <div class="artifact-list">${clips}</div>
          `
          : ""
      }
    </article>
  `;
}

export function renderLiveJobs(emptyState, results, jobs) {
  emptyState.hidden = jobs.length > 0;
  results.hidden = jobs.length === 0;
  results.innerHTML = jobs.map(renderJob).join("");
}
