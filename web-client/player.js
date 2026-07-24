const el = id => document.getElementById(id);
const storyId = new URLSearchParams(location.search).get('story') || 'lost-starlight';
let ws, currentEvent, sessionId, speaking = false;

function connect() {
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${scheme}://${location.host}/ws`);
  ws.onopen = () => { el('dot').classList.add('online'); el('connection').textContent = '本地演示已连接'; };
  ws.onclose = () => { el('dot').classList.remove('online'); el('connection').textContent = '连接已断开'; };
  ws.onmessage = event => handle(JSON.parse(event.data));
}
function send(type, extra={}) { if (ws?.readyState === 1) ws.send(JSON.stringify({type, ...extra})); }
function speak(text, done) {
  speaking = true;
  if ('speechSynthesis' in window && window.speechSynthesis) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text); utterance.lang = 'zh-CN'; utterance.rate = .92;
    utterance.onend = utterance.onerror = () => { speaking = false; done?.(); };
    window.speechSynthesis.speak(utterance);
  } else setTimeout(() => { speaking = false; done?.(); }, Math.max(1200, text.length * 120));
}
function setInput(show) { el('inputRow').style.display = show ? 'grid' : 'none'; el('prompt').style.display = show ? 'block' : 'none'; }
function handle(event) {
  currentEvent = event;
  if (event.progress !== undefined) el('progress').style.width = `${event.progress}%`;
  if (event.type === 'session_started') { sessionId = event.session_id; return; }
  if (event.type === 'story_sentence') {
    setInput(false); el('state').textContent = '故事正在讲述'; el('sentence').textContent = event.text; el('interrupt').disabled = false;
    speak(event.text, () => send('sentence_complete'));
  } else if (event.type === 'interaction_prompt') {
    el('interrupt').disabled = true; el('state').textContent = '轮到你表达'; el('sentence').textContent = event.text; el('prompt').textContent = '可以打字回答。真实产品中这里接入 ASR。'; setInput(true); speak(event.text);
  } else if (event.type === 'story_paused') {
    el('state').textContent = '故事已暂停'; el('sentence').textContent = event.text; el('prompt').textContent = '你想问什么？'; setInput(true); el('message').focus();
  } else if (event.type === 'assistant_answer') {
    setInput(false); el('state').textContent = 'AI 伙伴回答'; el('sentence').textContent = event.text; speak(event.text, () => send('answer_complete'));
  } else if (event.type === 'story_resumed') {
    el('state').textContent = event.text;
  } else if (event.type === 'story_end') {
    window.speechSynthesis?.cancel(); setInput(false); el('progress').style.width = '100%'; el('state').textContent = '故事完成'; el('sentence').textContent = '谢谢你的认真倾听和表达。互动报告已经生成。'; el('interrupt').disabled = true; el('start').textContent = '查看互动报告'; el('start').style.display = 'inline-flex'; el('start').onclick = () => location.href = `/report.html?session=${sessionId}`;
  } else if (event.type === 'error') { el('state').textContent = '操作提示'; el('sentence').textContent = event.message; }
}
el('start').onclick = () => { send('start_story', {story_id: storyId}); el('start').style.display = 'none'; };
el('interrupt').onclick = () => { if (currentEvent?.type === 'story_sentence') { window.speechSynthesis?.cancel(); speaking = false; send('interrupt_intent'); } };
el('send').onclick = () => { const text = el('message').value.trim(); if (text) { send('user_message', {text}); el('message').value = ''; } };
el('message').addEventListener('keydown', e => { if (e.key === 'Enter') el('send').click(); });
connect();
