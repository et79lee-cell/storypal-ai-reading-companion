const session = new URLSearchParams(location.search).get('session');
const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
if (session) fetch(`/api/reports/${encodeURIComponent(session)}`).then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(report => {
  document.querySelector('#summary').innerHTML = `<div class="metric"><strong>${escapeHtml(report.progress)}%</strong>完成进度</div><div class="metric"><strong>${escapeHtml(report.interaction_count)}</strong>互动次数</div><div class="metric"><strong>本地</strong>数据模式</div>`;
  document.querySelector('#timeline').innerHTML = report.interactions.length ? report.interactions.map(item => `<div class="timeline-item"><strong>${item.kind === 'interrupt' ? '主动打断' : '引导互动'}</strong><p>孩子：${escapeHtml(item.child_text)}</p><p class="sub">伙伴：${escapeHtml(item.assistant_text)}</p></div>`).join('') : '<p class="sub">本次没有产生互动记录。</p>';
}).catch(() => document.querySelector('#timeline').innerHTML = '<p class="sub">会话不存在或本地服务已重启。请重新完成一次故事。</p>');
