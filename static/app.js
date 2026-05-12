const API = "/api";

async function request(method, path, body) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    if (res.status === 204) return null;
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail);
    }
    return res.json();
}

function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function renderTodos(todos) {
    const list = document.getElementById("todo-list");
    if (todos.length === 0) {
        list.innerHTML = '<li class="empty-state">No todos yet. Add one above!</li>';
        return;
    }
    list.innerHTML = todos
        .map(
            (t) => `
        <li class="todo-item ${t.completed ? "completed" : ""}" data-id="${t.id}">
          <input type="checkbox" class="todo-checkbox" ${t.completed ? "checked" : ""} />
          <div class="todo-content">
            <div class="todo-title">${escapeHtml(t.title)}</div>
            ${t.description ? `<div class="todo-desc">${escapeHtml(t.description)}</div>` : ""}
            <div class="todo-date">${formatDate(t.created_at)}</div>
          </div>
          <div class="todo-actions">
            <button class="btn-edit" onclick="editTodo(${t.id})">Edit</button>
            <button class="btn-delete" onclick="deleteTodo(${t.id})">Delete</button>
          </div>
        </li>`
        )
        .join("");
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadTodos() {
    try {
        const todos = await request("GET", "/todos");
        renderTodos(todos);
    } catch (e) {
        console.error("Failed to load todos:", e);
    }
}

async function loadStats() {
    try {
        const s = await request("GET", "/stats");
        document.getElementById("stat-total").textContent = s.total;
        document.getElementById("stat-done").textContent = s.completed;
        document.getElementById("stat-pending").textContent = s.pending;
        const cached = document.getElementById("stat-cached");
        if (s.cached_count !== undefined && s.cached_count !== null) {
            cached.textContent = `(cached: ${s.cached_count})`;
        } else {
            cached.textContent = "";
        }
    } catch (e) {
        console.error("Failed to load stats:", e);
    }
}

async function checkRedis() {
    const badge = document.getElementById("redis-badge");
    try {
        const h = await request("GET", "/health");
        if (h.redis_connected) {
            badge.textContent = "Redis: connected";
            badge.className = "badge connected";
        } else {
            badge.textContent = "Redis: disconnected";
            badge.className = "badge disconnected";
        }
    } catch {
        badge.textContent = "Redis: error";
        badge.className = "badge disconnected";
    }
}

async function addTodo(title, description) {
    await request("POST", "/todos", { title, description });
    await Promise.all([loadTodos(), loadStats()]);
}

async function deleteTodo(id) {
    await request("DELETE", `/todos/${id}`);
    await Promise.all([loadTodos(), loadStats()]);
}

async function editTodo(id) {
    const title = prompt("New title:");
    if (!title) return;
    const desc = prompt("New description (or leave empty):");
    await request("PUT", `/todos/${id}`, { title, description: desc || "" });
    await Promise.all([loadTodos(), loadStats()]);
}

document.getElementById("todo-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const titleInput = document.getElementById("todo-title");
    const descInput = document.getElementById("todo-desc");
    const title = titleInput.value.trim();
    if (!title) return;
    await addTodo(title, descInput.value.trim());
    titleInput.value = "";
    descInput.value = "";
});

document.getElementById("todo-list").addEventListener("change", async (e) => {
    if (e.target.classList.contains("todo-checkbox")) {
        const li = e.target.closest(".todo-item");
        const id = Number(li.dataset.id);
        const completed = e.target.checked;
        await request("PUT", `/todos/${id}`, { completed });
        li.classList.toggle("completed", completed);
        await loadStats();
    }
});

async function init() {
    await Promise.all([checkRedis(), loadTodos(), loadStats()]);
}

init();
