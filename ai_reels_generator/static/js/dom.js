export function getElements() {
  return {
    form: document.getElementById("uploadForm"),
    input: document.getElementById("videos"),
    dropzone: document.getElementById("dropzone"),
    browseLink: document.getElementById("browseLink"),
    fileList: document.getElementById("fileList"),
    errorBox: document.getElementById("errorBox"),
    warningBox: document.getElementById("warningBox"),
    results: document.getElementById("results"),
    statusBox: document.getElementById("statusBox"),
    statusText: document.getElementById("statusText"),
    progressBar: document.getElementById("progressBar"),
    submitButton: document.getElementById("submitButton"),
    emptyState: document.getElementById("emptyState"),
  };
}
