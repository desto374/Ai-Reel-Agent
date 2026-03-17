export function showError(errorBox, message) {
  errorBox.hidden = false;
  errorBox.textContent = message;
}

export function clearError(errorBox) {
  errorBox.hidden = true;
  errorBox.textContent = "";
}

export function showWarning(warningBox, message) {
  warningBox.hidden = false;
  warningBox.textContent = message;
}

export function clearWarning(warningBox) {
  warningBox.hidden = true;
  warningBox.textContent = "";
}

export function setStatus(statusBox, statusText, progressBar, message, progress) {
  statusBox.hidden = false;
  statusText.textContent = message;
  progressBar.style.width = `${progress}%`;
}

export function setIdleState(statusBox, statusText, progressBar) {
  statusBox.hidden = true;
  progressBar.style.width = "0%";
  statusText.textContent = "Waiting for upload…";
}

export function renderFiles(fileList, files) {
  fileList.innerHTML = "";
  Array.from(files || []).forEach((file) => {
    const item = document.createElement("div");
    item.className = "file-pill";
    item.textContent = `${file.name} (${Math.round((file.size / 1024 / 1024) * 10) / 10} MB)`;
    fileList.appendChild(item);
  });
}
