function badgeClass(status) {
  return ["badge", status || "queued"].join(" ");
}

function stageLabel(job) {
  if (job.status === "completed") {
    return "finished";
  }
  if (job.status === "failed") {
    return "failed";
  }
  return job.stage || "queued";
}

function progressLabel(job) {
  if (job.status === "completed") {
    return "Done";
  }
  if (job.status === "failed") {
    return "Stopped";
  }
  return `${job.progress}%`;
}

function linkButton(href, label) {
  if (!href) {
    return "";
  }
  return `<a class="artifact-link" href="${href}" download>${label}</a>`;
}

function artifactMarkup(clip) {
  const downloads = clip.download_urls || {};
  return `
    <div class="artifact">
      <strong>${clip.title}</strong>
      <small>
        ${clip.source_start}s to ${clip.source_end}s<br>
        ${clip.drive_link ? `Drive: <a href="${clip.drive_link}" target="_blank" rel="noreferrer">open export</a>` : "Drive: not uploaded"}
      </small>
      <div class="artifact-actions">
        ${linkButton(downloads.captioned, "Download reel")}
        ${linkButton(downloads.vertical, "Vertical")}
        ${linkButton(downloads.clip, "Source cut")}
        ${linkButton(downloads.srt, "Subtitles")}
      </div>
    </div>
  `;
}

function renderJob(job) {
  const resultDownloads = job.result?.download_urls || {};
  const clips = (job.result?.clips || []).map(artifactMarkup).join("");
  return `
    <article class="job-card">
      <div class="job-head">
        <div>
          <h3 class="job-title">${job.filename}</h3>
          <p class="job-subtitle">${job.status === "completed" ? "Finished. Files are ready below." : (job.result?.source_video || "Awaiting processed output")}</p>
        </div>
        <span class="${badgeClass(job.status)}">${job.status}</span>
      </div>

      <div class="job-meta">
        <div class="meta-tile">
          <span>Stage</span>
          <strong>${stageLabel(job)}</strong>
        </div>
        <div class="meta-tile">
          <span>Progress</span>
          <strong>${progressLabel(job)}</strong>
        </div>
      </div>

      ${job.error ? `<div class="error-text">${job.error}</div>` : ""}

      ${
        job.result
          ? `
            <div class="job-meta">
              <div class="meta-tile">
                <span>Transcript</span>
                <strong>${resultDownloads.transcript ? `<a class="inline-link" href="${resultDownloads.transcript}" download>Download transcript</a>` : job.result.transcript_path}</strong>
              </div>
              <div class="meta-tile">
                <span>Manifest</span>
                <strong>${resultDownloads.manifest ? `<a class="inline-link" href="${resultDownloads.manifest}" download>Download manifest</a>` : job.result.manifest_path}</strong>
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
