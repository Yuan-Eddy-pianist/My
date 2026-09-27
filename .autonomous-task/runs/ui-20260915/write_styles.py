from pathlib import Path
p=Path('app/styles.css')
base=Path('.autonomous-task/runs/ui-20260915/baseline/styles.css').read_text()
voice=base[base.index('/* All icon faces'):base.index('/* ---- Todos page ---- */')]
s='''/* My — a quiet workspace for focus and everyday work. */
:root {
  color-scheme: light;
  --bg: #f6f5f0;
  --surface: #fffefa;
  --ink: #25372f;
  --muted: #657268;
  --line: #dce1d7;
  --accent: #315b46;
  --accent-deep: #224634;
  --accent-soft: #e9efe6;
  --accent-bright: #789c7d;
  --warn: #925310;
  --danger: #ae3e37;
  --done: #6b766e;
  --radius: 18px;
  --ctrl-h: 42px;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-display: Georgia, "Times New Roman", serif;
}
* { box-sizing: border-box; }
html { min-height: 100%; scroll-behavior: smooth; }
body { margin: 0; min-height: 100vh; background: var(--bg); color: var(--ink); font: 15px/1.6 var(--font-body); -webkit-font-smoothing: antialiased; }
body.break-mode { --accent: #3d6380; --accent-deep: #2c4f69; --accent-soft: #e9eff3; --accent-bright: #7a9bb2; --bg: #f2f5f5; }
a { color: inherit; text-decoration: none; }
button, input, select { font: inherit; }
button, .btn { appearance: none; border: 1px solid transparent; border-radius: 10px; min-height: 40px; padding: 9px 16px; color: var(--ink); font-size: 14px; font-weight: 600; cursor: pointer; transition: background .18s, border-color .18s, box-shadow .18s; }
button:hover { filter: brightness(.96); }
button:disabled { opacity: .5; cursor: not-allowed; filter: none; }
:where(a, button, input, select, summary):focus-visible { outline: 3px solid var(--accent); outline-offset: 4px; }
::selection { background: var(--accent-soft); }
.shell { width: min(1120px, calc(100% - 64px)); margin: 0 auto; padding: 28px 0 40px; }
.skip-link { position: absolute; left: 20px; top: -100px; z-index: 10; background: var(--ink); color: white; padding: 12px 20px; border-radius: 8px; }
.skip-link:focus { top: 12px; }
.topbar { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 28px; padding-bottom: 22px; border-bottom: 1px solid var(--line); }
.brand { justify-self: start; font: italic 600 34px/1 var(--font-display); letter-spacing: -2px; }
.brand-dot { color: var(--accent-bright); }
.nav { display: flex; align-items: center; gap: 4px; padding: 4px; background: #eaece5; border-radius: 12px; }
.nav a { padding: 8px 25px; min-height: 38px; color: var(--muted); border-radius: 9px; font-size: 14px; font-weight: 600; white-space: nowrap; }
.nav a.active { color: var(--accent-deep); background: var(--surface); box-shadow: 0 1px 4px #23362c0b; }
.nav a:hover { color: var(--accent); }
.topbar-end { justify-self: end; display: flex; align-items: center; gap: 14px; }
.clock-badge { display: inline-flex; align-items: center; gap: 8px; padding: 7px 12px; min-height: 38px; background: transparent; border-color: var(--line); border-radius: 9px; color: var(--muted); font-size: 12px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.clock-badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: #a1aaa0; }
.clock-badge[data-running="1"] { color: var(--accent-deep); background: var(--accent-soft); border-color: transparent; }
.clock-badge[data-running="1"]::before { background: var(--accent); }
.voice-controls { position: relative; display: flex; align-items: center; flex: none; }
.btn-mic { display: grid; place-items: center; flex: none; width: var(--ctrl-h); height: var(--ctrl-h); min-height: var(--ctrl-h); padding: 0; background: var(--accent); color: #fffefa; border-radius: 50%; }
.voice-status-row { min-height: 40px; display: flex; justify-content: flex-end; padding-top: 8px; }
.voice-status { color: var(--muted); font-size: 11px; text-align: right; max-width: 100%; overflow-wrap: anywhere; }
.voice-status[data-state="error"] { color: var(--danger); }
.voice-status[data-state="recording"] { color: var(--danger); font-weight: 600; }
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); }
.eyebrow { margin: 0 0 12px; color: var(--accent); font-size: 12px; font-weight: 600; letter-spacing: .12em; }
.focus-page { max-width: 760px; margin: 12px auto 0; }
.focus-heading { text-align: center; margin-bottom: 30px; }
h1 { font-size: 32px; line-height: 1.35; letter-spacing: -.035em; font-weight: 600; }
.focus-heading h1 { margin: 0 0 12px; }
.focus-heading > p:last-child { color: var(--muted); font-size: 14px; margin: 0; }
.hero { padding: 36px 28px 0; text-align: center; box-shadow: 0 8px 30px #34463804; }
.clock-face { --ring: var(--accent); --hand: var(--accent); --tick: #acb8aa; position: relative; width: min(320px, 100%); margin: 0 auto 27px; }
.clock-face.break { --tick: #a0b3c0; }
.clock-svg { width: 100%; height: auto; display: block; }
.clock-dial { fill: var(--surface); stroke: none; }
.tick.major { stroke: var(--tick); stroke-width: 1.2; stroke-linecap: round; }
.clock-track { fill: none; stroke: var(--accent-soft); stroke-width: 3; }
.clock-progress { fill: none; stroke: var(--ring); stroke-width: 3.5; stroke-linecap: round; transform: rotate(-90deg); transform-origin: 150px 150px; transition: stroke-dashoffset .25s linear; }
.clock-hand { stroke: var(--hand); stroke-width: 2.3; stroke-linecap: round; }
.clock-content { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; pointer-events: none; }
.mode-label { color: var(--accent); font-size: 12px; font-weight: 600; letter-spacing: .2em; margin-bottom: 6px; }
.timer-value { font-size: clamp(58px, 8vw, 76px); font-weight: 400; line-height: 1.1; letter-spacing: -.055em; font-variant-numeric: tabular-nums; }
.timer-hint { color: var(--muted); font-size: 12px; margin-top: 16px; }
.controls { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 10px; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-deep); }
.btn-secondary { background: var(--accent-soft); color: var(--accent-deep); }
.btn-ghost { border-color: var(--line); background: transparent; color: var(--muted); }
.controls button { min-height: 46px; padding-inline: 21px; }
.controls .btn-primary { min-width: 154px; }
.controls .btn-ghost { border-color: transparent; }
.meta-row { margin: 34px -28px 0; padding: 18px 24px; border-top: 1px solid var(--line); display: flex; justify-content: space-between; align-items: center; gap: 16px; font-size: 12px; color: var(--muted); }
.meta-row strong { color: var(--ink); font-weight: 500; }
.meta-dot { margin-inline: 8px; color: #9ca698; }
.focus-footer { margin: 20px 0 0; text-align: center; color: var(--muted); font-size: 12px; }
/* Workspace */
.page-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; margin: 12px 0 30px; }
.page-head h1 { margin: 0 0 10px; font-size: 36px; }
.page-head .eyebrow { margin-bottom: 8px; }
.page-head p:last-child { margin: 0; font-size: 13px; color: var(--muted); }
#lists { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr); gap: 32px 28px; align-items: start; }
.workspace-section { min-width: 0; }
.projects-section { grid-column: 1 / -1; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 0 13px; min-height: 36px; }
.section-label { display: flex; align-items: center; gap: 10px; margin: 0; font-size: 16px; font-weight: 600; }
.section-count { min-width: 23px; padding: 1px 6px; text-align: center; background: var(--accent-soft); color: var(--accent); border-radius: 6px; font-size: 11px; font-weight: 600; }
.section-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.btn-tiny { min-height: 34px; padding: 6px 10px; font-size: 12px; border-radius: 8px; }
.section-head .btn-ghost { border-color: transparent; }
.list { padding: 4px 18px; }
.task { display: grid; grid-template-columns: 22px minmax(0, 1fr) auto; align-items: start; gap: 12px; padding: 18px 0; border-bottom: 1px solid var(--line); }
.task:last-child { border-bottom: 0; }
.task.done .task-title { color: var(--done); text-decoration: line-through; }
.task-title { display: block; margin: 0; font-size: 14px; font-weight: 550; line-height: 1.6; overflow-wrap: anywhere; }
label.task-title { cursor: pointer; }
.task-meta { margin: 5px 0 0; font-size: 12px; line-height: 1.65; color: var(--muted); overflow-wrap: anywhere; white-space: pre-wrap; }
.due-label { display: inline-block; font-size: 11px; border-radius: 5px; }
.due-label.overdue, .due-label.soon { padding: 1px 6px; }
.overdue { color: var(--danger); }
.soon { color: var(--warn); }
.due-label.overdue { background: #faeee9; }
.due-label.soon { background: #f7f0df; }
.check { width: 18px; height: 18px; margin: 3px 0 0; accent-color: var(--accent); cursor: pointer; }
.btn-remove { align-self: center; color: var(--muted); padding: 5px; min-height: 32px; border-color: transparent; }
.btn-remove:hover { color: var(--danger); background: #faeee9; }
.empty { padding: 36px 24px; color: var(--muted); font-size: 13px; text-align: center; }
.empty strong { display: block; margin-bottom: 5px; color: var(--ink); font-size: 14px; font-weight: 500; }
.completed-list { margin-top: 12px; }
.project-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.project { min-width: 0; padding: 22px; }
.project-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.project-top > div { min-width: 0; }
.project .task-title { font-size: 16px; font-weight: 600; }
.project.done .task-title { color: var(--done); }
.project-kind { color: var(--muted); font-size: 10px; letter-spacing: .08em; margin: 0 0 5px; }
.status-select { border: 1px solid var(--line); border-radius: 7px; color: var(--accent); background: var(--accent-soft); min-height: 32px; padding: 4px 5px 4px 8px; font-size: 11px; cursor: pointer; max-width: 100%; }
.status-select[data-status="paused"] { color: var(--muted); background: #f0f0eb; }
.project-goal { color: var(--ink); font-size: 13px; line-height: 1.75; margin: 16px 0 12px; overflow-wrap: anywhere; }
.project-preview { color: var(--muted); font-size: 12px; line-height: 1.8; margin: 12px 0 16px; overflow-wrap: anywhere; }
.project-details { border-top: 1px solid var(--line); margin-top: 16px; padding-top: 12px; }
.project-details summary { cursor: pointer; color: var(--muted); font-size: 12px; padding: 4px 0; }
.project-details[open] summary { margin-bottom: 10px; color: var(--accent); }
.project-details .detail-label { font-size: 10px; font-weight: 600; color: var(--ink); margin: 14px 0 4px; }
.project-progress { white-space: pre-wrap; overflow-wrap: anywhere; color: var(--muted); font-size: 12px; line-height: 1.8; margin: 0; }
.path-text { margin: 0; font-size: 11px; line-height: 1.8; overflow-wrap: anywhere; color: var(--muted); }
.path-ok { color: var(--accent); }
.path-bad { color: var(--danger); }
.add-form { padding: 24px; margin-bottom: 18px; display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16px; background: #f0f3ec; }
.add-form label { display: grid; gap: 6px; min-width: 0; }
.add-form label:nth-child(3), .path-hint, .form-actions { grid-column: 1 / -1; }
.add-form label span { font-size: 12px; color: var(--ink); font-weight: 500; }
.add-form input { width: 100%; min-height: 44px; background: var(--surface); border: 1px solid #bbc6b9; color: var(--ink); border-radius: 8px; padding: 10px 12px; font-size: 14px; }
.add-form input::placeholder { color: #778273; }
.path-hint { font-size: 12px; margin: 0; overflow-wrap: anywhere; }
.path-hint:empty { display: none; }
.form-actions { display: flex; flex-wrap: wrap; gap: 10px; }
#lists > .empty { grid-column: 1 / -1; }
'''
s+='\n'+voice+'\n'
s+='''@media (max-width: 760px) {
  .shell { width: calc(100% - 36px); padding-top: 20px; }
  .topbar { grid-template-columns: 1fr auto; gap: 18px; padding-bottom: 14px; }
  .nav { grid-row: 2; grid-column: 1 / -1; justify-content: center; }
  .nav a { text-align: center; flex: 1; }
  .topbar-end { grid-row: 1; grid-column: 2; gap: 12px; }
  .voice-status-row { min-height: 36px; }
  .focus-page { margin-top: 15px; }
  .focus-heading { margin-bottom: 24px; }
  .focus-heading h1 { font-size: 26px; }
  .focus-heading > p:last-child { font-size: 12px; }
  .eyebrow { font-size: 11px; }
  .hero { padding: 25px 18px 0; }
  .clock-face { width: min(280px, 100%); margin-bottom: 23px; }
  .timer-value { font-size: 63px; }
  .controls { gap: 4px; }
  .controls button { padding-inline: 14px; }
  .controls .btn-primary { min-width: 128px; }
  .meta-row { margin: 25px -18px 0; padding: 16px; gap: 10px; font-size: 10px; }
  .meta-dot { margin-inline: 4px; }
  .focus-footer { font-size: 11px; margin-top: 16px; }
  .page-head { margin-top: 8px; margin-bottom: 24px; }
  .page-head h1 { font-size: 30px; }
  #lists { grid-template-columns: minmax(0,1fr); gap: 28px; }
  .project-list { grid-template-columns: minmax(0,1fr); }
  .project { padding: 20px; }
  .add-form { grid-template-columns: minmax(0,1fr); padding: 18px; }
  .list { padding-inline: 15px; }
  .task { gap: 10px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
'''
p.write_text(s)
