from pathlib import Path
root=Path('app')
# Shared header retains the same action IDs and voice icon state machinery.
old=(root/'index.html').read_text()
voice=old[old.index('            <button class="btn-mic"'):old.index('            </button>',old.index('            <button class="btn-mic"'))+len('            </button>')]
voice=voice.replace('aria-label="录音"','aria-label="开始语音记录" aria-describedby="voiceStatus" title="点击开始说话，再次点击结束"')
for name in ['index.html','todos.html']:
 p=root/name; s=p.read_text()
 a=s.index('    <link rel="preconnect"'); b=s.index('    <link rel="stylesheet" href="./styles.css"',a)
 s=s[:a]+s[b:] # Use local/system fonts; no font network dependency.
 a=s.index('      <header class="topbar">'); b=s.index('      </header>',a)+len('      </header>')
 nav=''.join(f'<a {"class=\"active\" aria-current=\"page\" " if dest==name else ""}href="./{dest}">{label}</a>' for dest,label in [('index.html','专注'),('todos.html','工作台')])
 header=f'''      <a class="skip-link" href="#main">跳到主要内容</a>
      <header class="topbar">
        <a class="brand" href="./index.html" aria-label="My 首页">My<span class="brand-dot" aria-hidden="true">.</span></a>
        <nav class="nav" aria-label="主导航">{nav}</nav>
        <div class="topbar-end">
          <button class="clock-badge" id="clockBadge" type="button">专注 35:00</button>
          <div class="voice-controls">
{voice}
          </div>
        </div>
      </header>
      <div class="voice-status-row"><span class="voice-status" id="voiceStatus" role="status">随时说一句，记下想做的事</span></div>'''
 s=s[:a]+header+s[b:]
 s=s.replace('micBtn: $("#micBtn"),','micBtn: $("#micBtn"),\n        statusEl: $("#voiceStatus"),')
 if name=='index.html':
  s=s.replace('<main class="panel hero">','''<main id="main" class="focus-page">
        <div class="focus-heading">
          <p class="eyebrow">给自己一段专注的时间</p>
          <h1>此刻，只做一件事。</h1>
          <p>35 分钟专注，5 分钟休息。找到自己的节奏。</p>
        </div>
        <section class="panel hero" aria-label="专注计时器">''')
  s=s.replace('y1="92"','y1="29"').replace('y2="40"','y2="38"')
  s=s.replace('          </svg>\n        </div>','''          </svg>
          <div class="clock-content">
            <span class="mode-label" id="timerMode">专注</span>
            <span class="timer-value" id="timerDisplay" role="timer" aria-label="剩余时间" aria-live="off">35:00</span>
            <span class="timer-hint" id="timerHint">准备好了，就开始</span>
          </div>
        </div>''',1)
  s=s.replace('type="button">开始</button>','type="button">开始专注</button>',1)
  s=s.replace('id="skipBtn" type="button"','id="skipBtn" type="button" title="跳过当前阶段"')
  s=s.replace('<span>35 / 5</span>','<span><strong>35</strong> 分钟专注 <span class="meta-dot">·</span> <strong>5</strong> 分钟休息</span>')
  s=s.replace('      </main>','''        </section>
        <p class="focus-footer">想起要做的事？点击右上角的麦克风，先记下来。</p>
      </main>''')
  s=s.replace('      setupPomodoro({','''      setupPomodoro({
        displayEl: $("#timerDisplay"),
        modeEl: $("#timerMode"),
        hintEl: $("#timerHint"),''')
 else:
  s=s.replace('      <div class="page-head">','      <main id="main">\n      <div class="page-head">',1)
  s=s.replace('          <h1>工作台</h1>','''          <p class="eyebrow">一件一件，慢慢完成</p>
          <h1>工作台</h1>
          <p id="workspaceSummary">正在整理你的工作台…</p>''')
  s=s.replace('<div id="lists"></div>','''<div id="lists" aria-busy="true"><div class="panel empty">正在加载项目、待办和提醒…</div></div>
      </main>''')
 p.write_text(s)
