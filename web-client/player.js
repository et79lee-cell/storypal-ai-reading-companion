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
function setInput(show, allowSkip=false) { el('inputRow').style.display = show ? 'grid' : 'none'; el('prompt').style.display = show ? 'block' : 'none'; el('skip').style.display = allowSkip ? 'inline-flex' : 'none'; }
function handle(event) {
  currentEvent = event;
  if (event.progress !== undefined) el('progress').style.width = `${event.progress}%`;
  if (event.type === 'session_started') { sessionId = event.session_id; return; }
  if (event.type === 'story_sentence') {
    setInput(false); el('state').textContent = '故事正在讲述 · 可以随时打断'; el('sentence').textContent = event.text; el('interrupt').disabled = false;
    speak(event.text, () => send('sentence_complete'));
  } else if (event.type === 'proactive_question') {
    const dimensions = (event.dimension_labels || []).join(' × ');
    el('interrupt').disabled = true; el('state').textContent = `AI 主动提问 · ${dimensions}`; el('sentence').textContent = event.text; el('prompt').textContent = event.question_design?.learning_goal || '可以打字回答，也可以稍后再说。'; setInput(true, event.skip_allowed); speak(event.text);
  } else if (event.type === 'story_paused') {
    el('state').textContent = '用户打断提问 · 故事已暂停'; el('sentence').textContent = event.text; el('prompt').textContent = '你想问什么？AI 会结合当前故事和本次互动记忆回答。'; setInput(true, false); el('message').focus();
  } else if (event.type === 'assistant_answer') {
    const moduleName = event.interaction_module === 'ai_proactive_question' ? '主动提问回应' : '打断问题回应';
    setInput(false); el('state').textContent = `AI 伙伴回答 · ${moduleName}`; el('sentence').textContent = event.text; speak(event.text, () => send('answer_complete'));
  } else if (event.type === 'story_resumed') {
    el('state').textContent = event.text;
  } else if (event.type === 'proactive_question_skipped') {
    setInput(false); el('state').textContent = '已略过这次主动提问';
  } else if (event.type === 'story_end') {
    window.speechSynthesis?.cancel(); setInput(false); el('progress').style.width = '100%'; el('state').textContent = '故事完成'; el('sentence').textContent = '谢谢你的认真倾听和表达。互动报告已经生成。'; el('interrupt').disabled = true; el('start').textContent = '查看互动报告'; el('start').style.display = 'inline-flex'; el('start').onclick = () => location.href = `/report.html?session=${sessionId}`;
  } else if (event.type === 'error') { el('state').textContent = '操作提示'; el('sentence').textContent = event.message; }
}
el('start').onclick = () => { send('start_story', {story_id: storyId}); el('start').style.display = 'none'; };
el('interrupt').onclick = () => { if (currentEvent?.type === 'story_sentence') { window.speechSynthesis?.cancel(); speaking = false; send('interrupt_intent'); } };
el('skip').onclick = () => { window.speechSynthesis?.cancel(); send('skip_proactive_question'); };
el('send').onclick = () => { const text = el('message').value.trim(); if (text) { send('user_message', {text}); el('message').value = ''; } };
el('message').addEventListener('keydown', e => { if (e.key === 'Enter') el('send').click(); });
connect();
