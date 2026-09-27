from pathlib import Path
p=Path('app/app.js'); s=p.read_text()
s=s.replace('  modeEl,\n  startBtn,','  modeEl,\n  hintEl,\n  startBtn,',1)
s=s.replace('const label = state.mode === "work" ? "Focus" : "Break";','const label = state.mode === "work" ? "专注" : "休息";',1)
s=s.replace('    setText(startBtn, state.running ? "暂停" : "开始");','''    const action = state.running ? "暂停" : remMs < totalMs ? "继续" : "开始";
    setText(startBtn, `${action}${label}`);
    setText(hintEl, state.running ? (state.mode === "work" ? "专心投入，时间会替你记着" : "放松一下，稍后继续") : remMs < totalMs ? "已暂停，按自己的节奏来" : "准备好了，就开始");
    if (startBtn) startBtn.setAttribute("aria-pressed", String(state.running));''',1)
s=s.replace('      setText(badgeEl, `${label} ${clock}`);','''      setText(badgeEl, `${label} ${clock}`);
      badgeEl.title = `${state.running ? "暂停" : "开始"}${label}计时 · 切换页面后继续计时`;
      badgeEl.setAttribute("aria-label", `${label}剩余 ${clock}，点击${state.running ? "暂停" : "开始"}`);
      badgeEl.setAttribute("aria-pressed", String(state.running));''',1)
s=s.replace('    badgeEl.title = "Pomodoro (keeps running across pages)";\n','')
s=s.replace('export function setupVoice({\n  micBtn,','export function setupVoice({\n  micBtn,\n  statusEl,',1)
s=s.replace('  let prevState = "";','''  let prevState = "";

  function feedback(text, state = "idle") {
    if (statusEl) {
      statusEl.textContent = text;
      statusEl.dataset.state = state;
    }
    micBtn.setAttribute("aria-label", listening ? "结束语音记录" : "开始语音记录");
    micBtn.setAttribute("aria-pressed", String(listening));
  }
  feedback("随时说一句，记下想做的事");''',1)
s=s.replace('micBtn.style.transform = `scale(${(1 + (pct / 100) * 0.35).toFixed(3)})`;','''if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            micBtn.style.transform = `scale(${(1 + (pct / 100) * 0.2).toFixed(3)})`;
          }''',1)
s=s.replace('  function flashIcon(cls, ms) {','  function flashIcon(cls, ms, message) {',1)
s=s.replace('    micBtn.classList.add(cls);\n    if (flashTimer)', '''    micBtn.classList.add(cls);
    feedback(message || (cls === "done-flash" ? "已整理到工作台" : "语音记录失败，请重试"), cls === "done-flash" ? "done" : "error");
    if (flashTimer)''',1)
s=s.replace('    if (faceEl) faceEl.classList.toggle("breathing", on);','''    if (faceEl) faceEl.classList.toggle("breathing", on);
    if (on && !listening) feedback("正在整理语音…也可以继续记录", "processing");''',1)
s=s.replace('    // Pipeline feedback lives entirely on the mic button: spinning dots\n    // while the server pipeline works, then a ✓ morph (done) or :( (error).','    // Keep the text status and icon feedback in sync with the voice pipeline.')
s=s.replace('flashIcon("error-flash", 3200);\n    } finally {','flashIcon("error-flash", 3200, "发送失败，请检查连接后重试");\n    } finally {',1)
s=s.replace('      preferredDeviceId = "";\n      return;','      preferredDeviceId = "";\n      feedback("没有录到声音，请再试一次", "error");\n      return;',1)
s=s.replace('    micBtn.disabled = true;','    micBtn.disabled = true;\n    feedback("当前浏览器无法录音，请使用 Chrome 或 Edge", "error");',1)
s=s.replace('    try {\n      if (!preferredDeviceId) {','    try {\n      feedback("正在连接麦克风…", "connecting");\n      if (!preferredDeviceId) {',1)
s=s.replace('      micBtn.classList.add("listening");\n      wdEvent','      micBtn.classList.add("listening");\n      feedback("正在聆听…再次点击麦克风结束", "recording");\n      wdEvent',1)
s=s.replace('      wdEvent("recErr", err?.name || String(err));\n      flashIcon("error-flash", 3200);','''      wdEvent("recErr", err?.name || String(err));
      flashIcon("error-flash", 3200, err?.name === "NotAllowedError"
        ? "未获得麦克风权限，请在浏览器中允许后重试"
        : "无法连接麦克风，请检查设备后重试");''',1)
p.write_text(s)

p=Path('app/todos.html'); s=p.read_text()
s=s.replace('<label class="task ${item.status === "done" ? "done" : ""}">','<article class="task ${item.status === "done" ? "done" : ""}">')
s=s.replace('              class="check"\n','              class="check"\n              id="${kind}-${escapeAttr(item.id)}"\n',1)
s=s.replace('<p class="task-title">${escapeHtml(item.title || "(未命名)")}</p>','<label class="task-title" for="${kind}-${escapeAttr(item.id)}">${escapeHtml(item.title || "(未命名)")}</label>',1)
s=s.replace('<p class="task-meta ${meta.kind}">','<p class="task-meta"><span class="due-label ${meta.kind}">',1).replace('${escapeHtml(meta.text)}</p>','${escapeHtml(meta.text)}</span></p>',1)
s=s.replace('            ${removeBtn || "<div></div>"}\n          </label>','            ${removeBtn}\n          </article>',1)
s=s.replace('aria-label="删除">删除</button>','aria-label="删除${escapeAttr(item.title || "未命名事项")}">删除</button>',1)
a=s.index('      function projectCard(p) {'); b=s.index('      function render()',a)
s=s[:a]+'''      function projectCard(p) {
        const status = p.status || "active";
        const pathLabel = !p.path ? "未设置目录" : p._pathOk === false ? "目录不可用" : p._pathOk === true ? "已连接本机目录" : "本机目录";
        const pathClass = p._pathOk === false ? "path-bad" : "path-ok";
        const recent = recentProgress(p.progress);
        const preview = recent ? recent.split("\\n").filter(Boolean).at(-1) : (p.progress ? "最近 7 天没有更新。" : "还没有进度记录，用语音记下第一步。");
        const excerpt = preview.length > 140 ? preview.slice(0, 140) + "…" : preview;
        return `
          <article class="panel project ${status === "done" ? "done" : ""}" data-id="${escapeAttr(p.id)}">
            <div class="project-top">
              <div><p class="project-kind">长期项目</p><h3 class="task-title">${escapeHtml(p.title || "(未命名项目)")}</h3></div>
              <select class="status-select" data-status="${escapeAttr(status)}" data-project-status="${escapeAttr(p.id)}" aria-label="${escapeAttr(p.title || "未命名项目")}的状态">
                <option value="active" ${status === "active" ? "selected" : ""}>进行中</option>
                <option value="paused" ${status === "paused" ? "selected" : ""}>暂停</option>
                <option value="done" ${status === "done" ? "selected" : ""}>完成</option>
              </select>
            </div>
            ${p.goal ? `<p class="project-goal">${escapeHtml(p.goal)}</p>` : ""}
            <p class="project-preview">${escapeHtml(excerpt)}</p>
            <details class="project-details" data-project-details="${escapeAttr(p.id)}">
              <summary>项目详情与进展</summary>
              <p class="detail-label ${pathClass}">${escapeHtml(pathLabel)}</p>
              <p class="path-text">${escapeHtml(p.path || "尚未设置本机目录")}</p>
              ${recent ? `<p class="detail-label">最近 7 天</p><p class="project-progress">${escapeHtml(recent)}</p>` : ""}
            </details>
          </article>`;
      }

'''+s[b:]
s=s.replace('      function render() {','''      function render() {
        const focused = document.activeElement;
        const focusId = focused?.id;
        const focusProject = focused?.getAttribute("data-project-status");
        const draft = $("#projectForm") ? new FormData($("#projectForm")) : null;
        const expanded = new Set([...listsEl.querySelectorAll("details[open]")].map(el => el.dataset.projectDetails));''',1)
s=s.replace('<div class="panel list project-list">','<div class="project-list">')
s=s.replace('<div class="panel empty">还没有长期项目。用下方表单添加，并绑到本机项目目录。</div>','<div class="panel empty"><strong>给长期目标留个位置</strong>添加一个项目，连接本机目录，记录每一步进展。</div>')
s=s.replace('<div class="panel empty">没有短期待办。</div>','<div class="panel empty"><strong>眼前的事，都完成了</strong>有新的想法？点击麦克风记下来。</div>')
s=s.replace('<div class="panel empty">没有提醒。</div>','<div class="panel empty"><strong>暂时没有提醒</strong>需要记住的日期，用语音告诉我。</div>')
s=s.replace('id="pathHint">','id="pathHint" role="status">')
a=s.index('        listsEl.innerHTML = `'); b=s.index('        bindListEvents();',a)
s=s[:a]+'''        const dueCount = [...openTasks, ...openReminders].filter(item => item.due && item.due <= new Date().toLocaleDateString("en-CA")).length;
        $("#workspaceSummary").textContent = `${openTasks.length} 项待办 · ${openReminders.length} 个提醒${dueCount ? ` · ${dueCount} 项今天需要留意` : " · 按自己的节奏，推进每一天"}`;
        listsEl.setAttribute("aria-busy", "false");
        listsEl.innerHTML = `
          <section class="workspace-section" aria-labelledby="tasksHeading">
            <div class="section-head">
              <h2 class="section-label" id="tasksHeading">短期待办 <span class="section-count">${openTasks.length}</span></h2>
              ${doneTasks.length ? `<button class="btn-ghost btn-tiny" id="toggleDoneTasks" type="button" aria-expanded="${showDoneTasks}">${showDoneTasks ? "收起已完成" : `已完成 ${doneTasks.length}`}</button>` : ""}
            </div>
            ${taskRows}
            <div class="completed-list">${doneTaskBlock}</div>
          </section>
          <section class="workspace-section" aria-labelledby="remindersHeading">
            <div class="section-head">
              <h2 class="section-label" id="remindersHeading">提醒 <span class="section-count">${openReminders.length}</span></h2>
              ${doneReminders.length ? `<button class="btn-ghost btn-tiny" id="toggleDoneReminders" type="button" aria-expanded="${showDoneReminders}">${showDoneReminders ? "收起已完成" : `已完成 ${doneReminders.length}`}</button>` : ""}
            </div>
            ${reminderRows}
            <div class="completed-list">${doneReminderBlock}</div>
          </section>
          <section class="workspace-section projects-section" aria-labelledby="projectsHeading">
            <div class="section-head">
              <h2 class="section-label" id="projectsHeading">长期项目 <span class="section-count">${visibleProjects.length}</span></h2>
              <div class="section-actions">
                ${doneProjects.length ? `<button class="btn-ghost btn-tiny" id="toggleDoneProjects" type="button" aria-expanded="${showDoneProjects}">${showDoneProjects ? "收起已完成" : `已完成 ${doneProjects.length}`}</button>` : ""}
                <button class="btn-secondary btn-tiny" id="toggleProjectForm" type="button" aria-expanded="${projectFormOpen}">${projectFormOpen ? "收起表单" : "+ 添加项目"}</button>
              </div>
            </div>
            ${form}
            ${projectRows}
            <div class="completed-list">${doneProjectBlock}</div>
          </section>
        `;
        for (const detail of listsEl.querySelectorAll("details")) detail.open = expanded.has(detail.dataset.projectDetails);
        if (draft && $("#projectForm")) for (const [name, value] of draft) $("#projectForm").elements.namedItem(name).value = value;
'''+s[b:]
s=s.replace('        bindListEvents();\n      }','''        bindListEvents();
        const nextFocus = focusId ? document.getElementById(focusId) : focusProject ? [...listsEl.querySelectorAll("[data-project-status]")].find(el => el.dataset.projectStatus === focusProject) : null;
        nextFocus?.focus({ preventScroll: true });
      }''',1)
s=s.replace('            projectFormOpen = !projectFormOpen;\n            pathHint = "";\n            render();','''            projectFormOpen = !projectFormOpen;
            pathHint = "";
            render();
            if (projectFormOpen) $("#projectForm").elements.namedItem("title").focus();''',1)
s=s.replace('            projectFormOpen = false;\n            pathHint = "";\n            render();','''            projectFormOpen = false;
            pathHint = "";
            render();
            $("#toggleProjectForm")?.focus();''',1)
s=s.replace('                await load();','                await load();',1)
s=s.replace('      load().catch((err) => {\n        listsEl.innerHTML', '      load().catch((err) => {\n        listsEl.setAttribute("aria-busy", "false");\n        $("#workspaceSummary").textContent = "暂时无法连接，点击刷新再试一次。";\n        listsEl.innerHTML',1)
s=s.replace('}。serve.py 在运行吗？</div>`;', '}。请确认本地服务已启动，然后点击刷新。</div>`;',1)
p.write_text(s)
