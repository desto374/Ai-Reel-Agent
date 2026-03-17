import { pollJobs } from "./jobs.js";
import { clearError, renderFiles, setIdleState, setStatus, showError } from "./ui.js";

export function bindUploadFlow(elements, state) {
  const { browseLink, input, dropzone, form } = elements;

  browseLink.addEventListener("click", () => input.click());
  input.addEventListener("change", () => renderFiles(elements.fileList, input.files));

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
