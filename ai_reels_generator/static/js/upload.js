import { pollJobs } from "./jobs.js";
import {
  clearError,
  clearWarning,
  renderFiles,
  setIdleState,
  setStatus,
  showError,
  showWarning,
} from "./ui.js";

const WARNING_FILE_SIZE_BYTES = 200 * 1024 * 1024;
const WARNING_TOTAL_SIZE_BYTES = 500 * 1024 * 1024;

function formatFileSize(bytes) {
  return `${Math.round((bytes / 1024 / 1024) * 10) / 10} MB`;
}

function updateLargeFileWarning(warningBox, files) {
  const selectedFiles = Array.from(files || []);
  if (!selectedFiles.length) {
    clearWarning(warningBox);
    return;
  }

  const largeFiles = selectedFiles.filter((file) => file.size >= WARNING_FILE_SIZE_BYTES);
  const totalBytes = selectedFiles.reduce((sum, file) => sum + file.size, 0);

  if (!largeFiles.length && totalBytes < WARNING_TOTAL_SIZE_BYTES) {
    clearWarning(warningBox);
    return;
  }

  const fileSummary = largeFiles.length
    ? `Large files detected: ${largeFiles
        .slice(0, 3)
        .map((file) => `${file.name} (${formatFileSize(file.size)})`)
        .join(", ")}. `
    : "";

  const totalSummary = totalBytes >= WARNING_TOTAL_SIZE_BYTES
    ? `Total upload size is ${formatFileSize(totalBytes)}. `
    : "";

  showWarning(
    warningBox,
    `${fileSummary}${totalSummary}Bigger uploads take longer to compress, split, transcribe, and render. Keep this tab open until the job cards finish updating.`,
  );
}

export function bindUploadFlow(elements, state) {
  const { browseLink, input, dropzone, form, warningBox } = elements;

  browseLink.addEventListener("click", () => input.click());
  input.addEventListener("change", () => {
    renderFiles(elements.fileList, input.files);
    updateLargeFileWarning(warningBox, input.files);
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (event) => {
    input.files = event.dataTransfer.files;
    renderFiles(elements.fileList, input.files);
    updateLargeFileWarning(warningBox, input.files);
  });

  dropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input.click();
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearError(elements.errorBox);
    updateLargeFileWarning(warningBox, input.files);
    elements.results.hidden = true;
    elements.results.innerHTML = "";

    if (!input.files || !input.files.length) {
      showError(elements.errorBox, "Choose at least one .mp4 or .mov file.");
      return;
    }

    const formData = new FormData(form);
    elements.submitButton.disabled = true;
    setStatus(elements.statusBox, elements.statusText, elements.progressBar, "Uploading files…", 0);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/");

    xhr.upload.addEventListener("progress", (progressEvent) => {
      if (!progressEvent.lengthComputable) {
        return;
      }
      const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
      setStatus(elements.statusBox, elements.statusText, elements.progressBar, `Uploading files… ${percent}%`, percent);
    });

    xhr.onreadystatechange = () => {
      if (xhr.readyState !== XMLHttpRequest.DONE) {
        return;
      }

      try {
        const payload = JSON.parse(xhr.responseText);
        if (xhr.status >= 400) {
          elements.submitButton.disabled = false;
          setIdleState(elements.statusBox, elements.statusText, elements.progressBar);
          showError(elements.errorBox, payload.error || "Upload failed.");
          return;
        }

        state.activeJobIds = payload.job_ids || [];
        setStatus(elements.statusBox, elements.statusText, elements.progressBar, "Upload complete. Starting jobs…", 100);
        pollJobs(state, elements);
      } catch (_error) {
        elements.submitButton.disabled = false;
        setIdleState(elements.statusBox, elements.statusText, elements.progressBar);
        showError(elements.errorBox, "The server returned an unexpected response.");
      }
    };

    xhr.onerror = () => {
      elements.submitButton.disabled = false;
      setIdleState(elements.statusBox, elements.statusText, elements.progressBar);
      showError(elements.errorBox, "Network error while uploading files.");
    };

    xhr.send(formData);
  });
}
