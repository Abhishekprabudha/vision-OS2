const film = document.getElementById('film');
const chapters = document.getElementById('chapters');
const nowPlaying = document.getElementById('nowPlaying');
const durationStat = document.getElementById('durationStat');
let timeline = [];

const stamp = (seconds) => {
  const total = Math.max(0, Math.round(seconds));
  const m = Math.floor(total / 60);
  const s = String(total % 60).padStart(2, '0');
  return `${m}:${s}`;
};

fetch('dist/timeline.json')
  .then((r) => {
    if (!r.ok) throw new Error('Timeline not rendered yet');
    return r.json();
  })
  .then((data) => {
    timeline = data.scenes || [];
    durationStat.textContent = stamp(data.duration || 0);
    chapters.innerHTML = timeline.map((scene, index) => `
      <button class="chapter" data-index="${index}" data-start="${scene.start}" style="--accent:${index % 4 === 0 ? '#6ee7f7' : index % 4 === 1 ? '#a78bfa' : index % 4 === 2 ? '#34d399' : '#fbbf24'}">
        <span class="chapter-time">${stamp(scene.start)} · ${scene.industry}</span>
        <h3>${scene.title}</h3>
        <p>Play this chapter</p>
      </button>
    `).join('');
    chapters.addEventListener('click', (event) => {
      const button = event.target.closest('.chapter');
      if (!button) return;
      film.currentTime = Number(button.dataset.start || 0);
      film.play();
    });
  })
  .catch(() => {
    chapters.innerHTML = '<div class="chapter"><h3>Render the film through GitHub Actions</h3><p>The chapter timeline appears automatically after the MP4 is generated.</p></div>';
  });

film.addEventListener('timeupdate', () => {
  if (!timeline.length) return;
  const index = timeline.findIndex((scene) => film.currentTime >= scene.start && film.currentTime < scene.end);
  document.querySelectorAll('.chapter').forEach((el, i) => el.classList.toggle('active', i === index));
  if (index >= 0) nowPlaying.textContent = `${timeline[index].industry} · ${timeline[index].title}`;
});
