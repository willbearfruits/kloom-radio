(function () {
  'use strict';
  var KEY = 'kloom_player';
  var state = null;
  var audio = null;

  window.KloomPlayer = {
    load:          load,
    setNowPlaying: setNowPlaying,
    togglePlay:    togglePlay,
    close:         close,
    seek:          seek,
    restore:       restore
  };

  /* ── public ──────────────────────────────────────── */

  function load(data) {
    killAudio();
    state = {
      id:      data.id,
      title:   data.title,
      series:  data.series  || '',
      date:    data.date    || '',
      type:    'local_audio',
      src:     data.src     || '',
      audio_url: data.audio_url || '',
      time:    0,
      playing: true
    };
    renderFull();
    audio = new Audio(state.audio_url || state.src);
    audio.autoplay = true;
    audio.addEventListener('timeupdate', tick);
    audio.addEventListener('ended',      onEnded);
    persist();
  }

  /* indicator only – used for Mixcloud / YouTube embeds.
     If local audio is currently playing we leave the player bar alone;
     the embed is an iframe we can't control anyway. */
  function setNowPlaying(data) {
    if (audio && !audio.paused) return;
    killAudio();
    state = {
      id:      data.id,
      title:   data.title,
      series:  data.series || '',
      date:    data.date   || '',
      type:    data.type,
      show_url: data.show_url || '',
      playing: true
    };
    renderIndicator();
  }

  function restore() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY));
      if (!s || s.type !== 'local_audio' || (!s.src && !s.audio_url)) return;
      state = s;
      state.playing = false;
      renderFull();
      syncBtn();
      audio = new Audio(state.audio_url || state.src);
      audio.addEventListener('timeupdate', tick);
      audio.addEventListener('ended',      onEnded);
      /* seek only after the browser knows the duration; earlier calls are silently dropped */
      audio.addEventListener('loadedmetadata', function onMeta() {
        audio.removeEventListener('loadedmetadata', onMeta);
        audio.currentTime = state.time || 0;
        tick(); // paint progress bar at the saved position
      });
      /* pulsing hint so user knows audio was playing */
      var mid = document.getElementById('kp-mid');
      if (mid) {
        var hint    = document.createElement('div');
        hint.id     = 'kp-resume';
        hint.className = 'kp-resume';
        hint.textContent = '\u25B6  TAP TO RESUME';
        mid.insertBefore(hint, mid.firstChild);
      }
    } catch (e) { /* ignore */ }
  }

  function togglePlay() {
    if (!audio) return;
    var hint = document.getElementById('kp-resume');
    if (hint) hint.parentNode.removeChild(hint);
    if (audio.paused) { audio.play();  state.playing = true;  }
    else              { audio.pause(); state.playing = false; }
    syncBtn();
    persist();
  }

  function close() {
    killAudio();
    state = null;
    var el = document.getElementById('kloom-player');
    if (el) el.classList.remove('active');
    localStorage.removeItem(KEY);
  }

  function seek(e) {
    if (!audio || !audio.duration) return;
    var bar  = document.getElementById('kp-progress');
    if (!bar) return;
    var rect = bar.getBoundingClientRect();
    audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
  }

  /* ── private ─────────────────────────────────────── */

  function killAudio() {
    if (audio) { audio.pause(); audio = null; }
  }

  function tick() {
    if (!audio || !state) return;
    state.time = audio.currentTime;
    var fill = document.getElementById('kp-fill');
    var time = document.getElementById('kp-time');
    if (fill && audio.duration)
      fill.style.width = (audio.currentTime / audio.duration * 100) + '%';
    if (time)
      time.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration);
  }

  function onEnded() {
    if (state) { state.playing = false; syncBtn(); persist(); }
  }

  function syncBtn() {
    var btn = document.getElementById('kp-play-btn');
    if (btn) btn.textContent = (state && state.playing) ? '\u23F8' : '\u25B6';
  }

  function persist() {
    if (state) localStorage.setItem(KEY, JSON.stringify(state));
  }

  function fmt(s) {
    if (!s || isNaN(s)) return '0:00';
    var m = Math.floor(s / 60), sec = Math.floor(s % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  /* ── render ──────────────────────────────────────── */

  function renderFull() {
    var el = document.getElementById('kloom-player');
    if (!el) return;
    el.classList.add('active');
    document.getElementById('kp-title').textContent = state.title;
    document.getElementById('kp-meta').textContent  = state.series + ' // ' + state.date;

    var btn = document.getElementById('kp-play-btn');
    if (btn) btn.style.display = '';

    var mid = document.getElementById('kp-mid');
    mid.innerHTML =
      '<div class="kp-progress-wrap">' +
        '<div class="kp-progress" id="kp-progress"><div class="kp-progress-fill" id="kp-fill"></div></div>' +
        '<span class="kp-time" id="kp-time">0:00 / 0:00</span>' +
      '</div>';
    document.getElementById('kp-progress').addEventListener('click', seek);
    syncBtn();
  }

  function renderIndicator() {
    var el = document.getElementById('kloom-player');
    if (!el) return;
    el.classList.add('active');
    document.getElementById('kp-title').textContent = state.title;
    document.getElementById('kp-meta').textContent  = state.series + ' // ' + state.date;

    var btn = document.getElementById('kp-play-btn');
    if (btn) btn.style.display = 'none';

    document.getElementById('kp-mid').innerHTML =
      '<a href="' + (state.show_url || 'shows/' + state.id + '.html') + '" class="kp-badge">\u25B6 PLAYING &nbsp; OPEN \u2192</a>';
  }

  /* auto-persist every 3 s while playing */
  setInterval(function () { if (audio && !audio.paused && state) persist(); }, 3000);

})();

/* ── Client-side search ──────────────────────────── */
(function () {
  var input = document.getElementById('kloom-search');
  if (!input) return;

  var shows = [];
  fetch('search-index.json')
    .then(function (r) { return r.json(); })
    .then(function (d) { shows = d; })
    .catch(function () {});

  input.addEventListener('input', function (e) {
    var q = e.target.value.toLowerCase().trim();

    /* toggle section headers */
    document.querySelectorAll('.section-header').forEach(function (h) {
      h.style.display = q ? 'none' : '';
    });

    document.querySelectorAll('.show-item').forEach(function (card) {
      if (!q) { card.style.display = ''; return; }
      var id   = card.id.replace('card-', '');
      var show = shows.find(function (s) { return s.id === id; });
      if (!show) { card.style.display = 'none'; return; }
      var haystack = [show.title, show.description, show.series, show.guest || '', show.tags.join(' ')].join(' ').toLowerCase();
      card.style.display = haystack.indexOf(q) !== -1 ? '' : 'none';
    });
  });
})();
