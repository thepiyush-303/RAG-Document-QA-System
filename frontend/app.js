const uploadForm = document.querySelector("#upload-form");
const uploadButton = document.querySelector("#upload-button");
const uploadStatus = document.querySelector("#upload-status");
const chatPanel = document.querySelector("#chat-panel");
const messages = document.querySelector("#messages");
const queryForm = document.querySelector("#query-form");
const queryInput = document.querySelector("#query-input");
const queryButton = document.querySelector("#query-button");
const resetButton = document.querySelector("#reset-button");
const userIdInput = document.querySelector("#user-id");
const chatIdInput = document.querySelector("#chat-id");
const fileInput = document.querySelector("#pdf-file");

let activeSession = null;

function setStatus(message, type = "") {
  uploadStatus.textContent = message;
  uploadStatus.className = `status${type ? ` is-${type}` : ""}`;
}

function setChatEnabled(enabled) {
  chatPanel.classList.toggle("is-disabled", !enabled);
  queryInput.disabled = !enabled;
  queryButton.disabled = !enabled;
}

function appendMessage(role, text, rationale = "") {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = role === "user" ? "You" : "Assistant";

  const body = document.createElement("p");
  body.textContent = text;

  article.append(meta, body);

  if (rationale) {
    const rationaleEl = document.createElement("div");
    rationaleEl.className = "rationale";
    rationaleEl.textContent = `Rationale: ${rationale}`;
    article.append(rationaleEl);
  }

  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

async function readError(response) {
  const text = await response.text();
  if (!text) {
    return `${response.status} ${response.statusText}`;
  }

  try {
    const data = JSON.parse(text);
    return data.detail || data.message || text;
  } catch {
    return text;
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    setStatus("Select a PDF before uploading.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("user_id", userIdInput.value.trim());
  formData.append("chat_id", chatIdInput.value.trim());
  formData.append("file", file);

  uploadButton.disabled = true;
  setChatEnabled(false);
  setStatus("Uploading and vectorizing the PDF...");

  try {
    const response = await fetch("/ingest", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(await readError(response));
    }

    const data = await response.json();
    activeSession = {
      userId: userIdInput.value.trim(),
      chatId: chatIdInput.value.trim(),
      filename: file.name,
    };

    messages.innerHTML = "";
    appendMessage("assistant", data.message || `Ready to answer questions about ${file.name}.`);
    setStatus(`Ready: ${file.name}`, "success");
    setChatEnabled(true);
    queryInput.focus();
  } catch (error) {
    activeSession = null;
    setStatus(error.message || "PDF upload failed.", "error");
  } finally {
    uploadButton.disabled = false;
  }
});

queryForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!activeSession) {
    setStatus("Upload a PDF before asking questions.", "error");
    return;
  }

  const query = queryInput.value.trim();
  if (!query) {
    return;
  }

  appendMessage("user", query);
  queryInput.value = "";
  queryButton.disabled = true;
  const loadingMessage = appendMessage("assistant", "Thinking...", "");
  loadingMessage.classList.add("loading");

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        user_id: activeSession.userId,
        chat_id: activeSession.chatId,
        top_k: 5,
      }),
    });

    if (!response.ok) {
      throw new Error(await readError(response));
    }

    const data = await response.json();
    loadingMessage.remove();
    appendMessage("assistant", data.answer || "No answer returned.", data.rationale || "");
  } catch (error) {
    loadingMessage.remove();
    appendMessage("assistant", error.message || "Query failed.");
  } finally {
    queryButton.disabled = false;
    queryInput.focus();
  }
});

resetButton.addEventListener("click", () => {
  activeSession = null;
  uploadForm.reset();
  messages.innerHTML = "";
  appendMessage("assistant", "Upload a PDF to begin asking questions from its content.");
  setStatus("");
  setChatEnabled(false);
  userIdInput.focus();
});
