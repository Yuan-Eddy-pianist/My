"""Isolated UI preview: real workspace handler, disposable data, simulated voice."""
from pathlib import Path
import sys, json, time
from datetime import date, timedelta
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import serve
RUN=Path(__file__).resolve().parent
DATA=RUN/'preview-data'
DATA.mkdir(exist_ok=True)
serve.DATA=DATA
for attr,filename in [('WORKSPACE','todos.json'),('INBOX','inbox.md'),('INBOX_PENDING','pending.md'),('ARCHIVE','archive.md'),('STATUS','status.json'),('PROGRESS_STATE','progress.json')]:
 setattr(serve,attr,DATA/filename)
today=date.today(); yesterday=today-timedelta(days=1)
fixture={
 'projects':[
  {'id':'project-a','title':'个人作品集','path':str(ROOT),'goal':'整理近期作品，让每一次尝试都有迹可循。','status':'active','progress':f'{yesterday}：完成作品分类和首页草稿。\n{today}：继续打磨作品介绍，挑选三件最能代表自己的作品。'},
  {'id':'project-b','title':'阅读与写作','path':str(ROOT/'app'),'goal':'每周读完一本书，留下自己的思考。','status':'paused','progress':f'{today}：读完第一章，整理了三个值得继续思考的问题。'},
  {'id':'project-done','title':'夏日照片整理','path':str(ROOT),'status':'done','goal':'给夏天留下一份记录。','progress':''}
 ],
 'tasks':[
  {'id':'task-a','title':'整理本周的工作笔记','due':str(today),'status':'open','notes':'把零散的想法，整理成下一步行动。'},
  {'id':'task-b','title':'回复作品集的修改建议','due':str(yesterday),'status':'open','notes':''},
  {'id':'task-c','title':'读完正在看的那一章','due':None,'status':'open','notes':''},
  {'id':'task-done','title':'收拾书桌','due':str(today),'status':'done','notes':''}
 ],
 'reminders':[
  {'id':'reminder-a','title':'和朋友见面喝咖啡','due':str(today+timedelta(days=2)),'status':'open','notes':'下午三点，老地方。'},
  {'id':'reminder-b','title':'预约下周的课程','due':str(today),'status':'open','notes':''},
  {'id':'reminder-done','title':'取回借出的书','due':str(today),'status':'done','notes':''}
 ]}
(RUN/'fixture.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2))
if not serve.WORKSPACE.exists(): serve.write_workspace(fixture)
voice_started=0
MOCK='''<script>
window.Notification = undefined;
const previewDenied = new URLSearchParams(location.search).get('voice') === 'denied';
Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', {value:async()=>[{kind:'audioinput',label:'MacBook built-in microphone',deviceId:'preview'}]});
Object.defineProperty(navigator.mediaDevices, 'getUserMedia', {value:async()=>{
 if(previewDenied) throw new DOMException('Preview permission denied','NotAllowedError');
 const context=new AudioContext(), oscillator=context.createOscillator(), dest=context.createMediaStreamDestination();
 oscillator.frequency.value=220; oscillator.connect(dest); oscillator.start();
 const track=dest.stream.getAudioTracks()[0], stop=track.stop.bind(track);
 track.stop=()=>{stop();oscillator.stop();context.close();};
 return dest.stream;
}});
</script>'''
class PreviewHandler(serve.Handler):
 def log_message(self,*args): pass
 def do_GET(self):
  global voice_started
  path=urlparse(self.path).path
  if path=='/api/agent':
   if not voice_started: state='idle'
   else:
    elapsed=time.monotonic()-voice_started
    state='transcribing' if elapsed<3 else 'running' if elapsed<7 else 'done'
   self._send_json(200,{'state':state,'voicePending':int(state=='transcribing'),'agentPending':int(state=='running')})
  elif path.startswith('/app/') and path.endswith('.html'):
   file=(ROOT/path.lstrip('/')).resolve()
   if file.parent != ROOT/'app' or not file.is_file(): self._send(404,b'Not found','text/plain');return
   html=file.read_text().replace('<head>','<head>'+MOCK,1)
   self._send(200,html.encode(),'text/html; charset=utf-8')
  elif path in ('/','/api/workspace','/api/todos','/api/path') or path in ('/app/app.js','/app/styles.css'):
   super().do_GET()
  elif path=='/favicon.ico': self._send(204,b'','image/x-icon')
  else: self._send(404,b'Not found','text/plain')
 def do_POST(self):
  global voice_started
  if urlparse(self.path).path=='/api/voice':
   self._read_body();voice_started=time.monotonic();self._send_json(200,{'ok':True,'queued':True})
  elif urlparse(self.path).path in ('/api/workspace','/api/todos'):super().do_POST()
  else:self._send_json(404,{'error':'Unavailable in sample preview'})
print('Sample preview: http://127.0.0.1:8875/app/index.html',flush=True)
serve.ThreadingHTTPServer(('127.0.0.1',8875),PreviewHandler).serve_forever()
