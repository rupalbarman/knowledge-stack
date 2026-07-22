// Dev-only auth: paste a token from `POST /auth/login` here
const JWT_TOKEN = "dummy";

async function apiFetch(path) {
  const res = await fetch(path, {
    headers: { Authorization: `Bearer ${JWT_TOKEN}` },
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json();
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function createFolderNode(node, depth) {
  const li = document.createElement("li");

  const label = document.createElement("div");
  label.textContent = node.name;
  label.className = "folder-item";
  label.style.paddingLeft = `${0.6 + depth * 1}rem`;
  label.addEventListener("click", () =>
    selectFolder(node.id, node.name, label),
  );
  li.appendChild(label);

  if (node.children && node.children.length > 0) {
    const childList = document.createElement("ul");
    childList.className = "folder-list";
    for (const child of node.children) {
      childList.appendChild(createFolderNode(child, depth + 1));
    }
    li.appendChild(childList);
  }

  return li;
}

function renderFolders(tree) {
  const list = document.getElementById("folder-list");
  list.innerHTML = "";

  const rootItem = document.createElement("li");
  const rootLabel = document.createElement("div");
  rootLabel.textContent = "(root)";
  rootLabel.className = "folder-item active";
  rootLabel.addEventListener("click", () =>
    selectFolder(null, "(root)", rootLabel),
  );
  rootItem.appendChild(rootLabel);
  list.appendChild(rootItem);

  for (const node of tree) {
    list.appendChild(createFolderNode(node, 0));
  }

  selectFolder(null, "(root)", rootLabel);
}

function renderFiles(files, folderName) {
  document.getElementById("files-title").textContent = `Files in ${folderName}`;
  const tbody = document.getElementById("files-body");
  tbody.innerHTML = "";

  if (files.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="4" class="empty">No files</td>`;
    tbody.appendChild(row);
    return;
  }

  for (const file of files) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${file.name}</td>
      <td>${file.content_type ?? "-"}</td>
      <td>${formatBytes(file.size_bytes)}</td>
      <td>${new Date(file.created_at).toLocaleString()}</td>
    `;
    tbody.appendChild(row);
  }
}

let currentFolder = { id: null, name: "(root)" };

async function loadFilesForCurrentFolder() {
  try {
    const query = currentFolder.id ? `?folder_id=${currentFolder.id}` : "";
    const files = await apiFetch(`/files${query}`);
    renderFiles(files, currentFolder.name);
  } catch (err) {
    renderFiles([], currentFolder.name);
    document.getElementById("files-title").textContent =
      `Error loading files for ${currentFolder.name}: ${err.message}`;
  }
}

async function selectFolder(folderId, folderName, itemEl) {
  document
    .querySelectorAll(".folder-item")
    .forEach((el) => el.classList.remove("active"));
  itemEl.classList.add("active");

  currentFolder = { id: folderId, name: folderName };
  document.getElementById("upload-target").textContent = folderName;
  await loadFilesForCurrentFolder();
}

async function uploadSelectedFile() {
  const input = document.getElementById("upload-input");
  const status = document.getElementById("upload-status");
  const file = input.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  if (currentFolder.id) {
    formData.append("folder_id", currentFolder.id);
  }

  status.textContent = "Uploading...";
  try {
    const res = await fetch("/files", {
      method: "POST",
      headers: { Authorization: `Bearer ${JWT_TOKEN}` },
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `${res.status} ${res.statusText}`);
    }
    status.textContent = "";
    input.value = "";
    await loadFilesForCurrentFolder();
  } catch (err) {
    status.textContent = `Upload failed: ${err.message}`;
  }
}

document
  .getElementById("upload-btn")
  .addEventListener("click", uploadSelectedFile);

async function loadFolders() {
  try {
    const tree = await apiFetch("/folders/tree");
    renderFolders(tree);
  } catch (err) {
    document.getElementById("folder-list").innerHTML =
      `<li class="folder-item empty">Error: ${err.message}</li>`;
  }
}

function renderTasks(tasks) {
  const tbody = document.getElementById("tasks-body");
  tbody.innerHTML = "";

  if (tasks.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = `<td colspan="6" class="empty">No tasks</td>`;
    tbody.appendChild(row);
    return;
  }

  for (const task of tasks) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${task.file_name}</td>
      <td>${task.type}</td>
      <td>${task.reason}</td>
      <td>${task.status}</td>
      <td>${task.error ?? "-"}</td>
      <td>${new Date(task.created_at).toLocaleString()}</td>
    `;
    tbody.appendChild(row);
  }
}

const TASKS_PAGE_SIZE = 20;
let tasksOffset = 0;
let tasksTotal = 0;

function renderTasksPagination() {
  const info = document.getElementById("tasks-page-info");
  const prevBtn = document.getElementById("tasks-prev-btn");
  const nextBtn = document.getElementById("tasks-next-btn");

  info.textContent =
    tasksTotal === 0
      ? "No tasks"
      : `${tasksOffset + 1}-${Math.min(tasksOffset + TASKS_PAGE_SIZE, tasksTotal)} of ${tasksTotal}`;

  prevBtn.disabled = tasksOffset <= 0;
  nextBtn.disabled = tasksOffset + TASKS_PAGE_SIZE >= tasksTotal;
}

async function loadTasks() {
  try {
    const page = await apiFetch(
      `/tasks?limit=${TASKS_PAGE_SIZE}&offset=${tasksOffset}`,
    );
    tasksTotal = page.total;
    renderTasks(page.items);
    renderTasksPagination();
  } catch (err) {
    document.getElementById("tasks-body").innerHTML =
      `<tr><td colspan="6" class="empty">Error: ${err.message}</td></tr>`;
  }
}

function goToPrevTasksPage() {
  tasksOffset = Math.max(0, tasksOffset - TASKS_PAGE_SIZE);
  loadTasks();
}

function goToNextTasksPage() {
  tasksOffset += TASKS_PAGE_SIZE;
  loadTasks();
}

document
  .getElementById("tasks-refresh-btn")
  .addEventListener("click", loadTasks);
document
  .getElementById("tasks-prev-btn")
  .addEventListener("click", goToPrevTasksPage);
document
  .getElementById("tasks-next-btn")
  .addEventListener("click", goToNextTasksPage);

loadFolders();
loadTasks();
