fetch('/api/stories').then(r => r.json()).then(stories => {
  const root = document.querySelector('#stories');
  if (!stories.length) return;
  root.innerHTML = stories.map(story => `<article class="story-card"><div class="cover">${story.emoji}</div><h3>${story.title}</h3><p>${story.summary}</p><div class="meta"><span class="pill">${story.age_range}</span><a href="/player.html?story=${encodeURIComponent(story.id)}">开始阅读 →</a></div></article>`).join('');
}).catch(() => {});
