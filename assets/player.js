(function () {
  'use strict';
  var KEY = 'kloom_player';
  var state = null;
  var audio = null;
  var widget = null;        // Mixcloud widget instance
  var ytPlayer = null;      // YouTube player instance
  var ytReady = false;
  var ytPendingSeek = null;

  window.KloomPlayer = {
    load:          load,
    setNowPlaying: setNowPlaying,  // legacy, now just calls load
    togglePlay:    togglePlay,
    close:         close,
    seek:          seek,
    restore:       restore
  };

  /* ── public ──────────────────────────────────────── */

  function load(data) {
    killAll();

    var type = data.type || 'local_audio';

    state = {
      id:        data.id,
      title:     data.title,
      series:    data.series   || '',
      date:      data.date     || '',
      type:      type,
      src:       data.src      || '',
      audio_url: data.audio_url || '',
      embed_url: data.embed_url || '',
      show_url:  data.show_url || '',
      time:      0,
      playing:   true
    };

    if (type === 'local_audio') {
      renderLocalAudio();
      audio = new Audio(state.audio_url || state.src);
      audio.autoplay = true;
      audio.addEventListener('timeupdate', tickLocalAudio);
      audio.addEventListener('ended', onEnded);
    } else if (type === 'embed') {
      renderMixcloud();
    } else if (type === 'youtube') {
      renderYouTube();
    }

    persist();
  }

  /* Legacy function - now just calls load */
  function setNowPlaying(data) {
    load(data);
  }

  function restore() {
    try {
      var s = JSON.parse(localStorage.getItem(KEY));
      if (!s || !s.id) return;

      state = s;
      state.playing = false; // don't autoplay on restore (browser policy)

      if (state.type === 'local_audio') {
        if (!state.src && !state.audio_url) return;
        renderLocalAudio();
        audio = new Audio(state.audio_url || state.src);
        audio.addEventListener('timeupdate', tickLocalAudio);
        audio.addEventListener('ended', onEnded);
        audio.addEventListener('loadedmetadata', function onMeta() {
          audio.removeEventListener('loadedmetadata', onMeta);
          audio.currentTime = state.time || 0;
          tickLocalAudio();
        });
        showResumeHint();
      } else if (state.type === 'embed' && state.embed_url) {
        renderMixcloud(state.time);
        showResumeHint();
      } else if (state.type === 'youtube' && state.embed_url) {
        renderYouTube(state.time);
        showResumeHint();
      }
    } catch (e) { /* ignore */ }
  }

  function togglePlay() {
    var hint = document.getElementById('kp-resume');
    if (hint) hint.parentNode.removeChild(hint);

    if (state.type === 'local_audio' && audio) {
      if (audio.paused) { audio.play(); state.playing = true; }
      else { audio.pause(); state.playing = false; }
      syncBtn();
    } else if (state.type === 'embed' && widget) {
      if (state.playing) {
        widget.pause();
        state.playing = false;
      } else {
        widget.play();
        state.playing = true;
      }
      syncBtn();
    } else if (state.type === 'youtube' && ytPlayer && ytReady) {
      var ytState = ytPlayer.getPlayerState();
      if (ytState === 1) { // playing
        ytPlayer.pauseVideo();
        state.playing = false;
      } else {
        ytPlayer.playVideo();
        state.playing = true;
      }
      syncBtn();
    }
    persist();
  }

  function close() {
    killAll();
    state = null;
    var el = document.getElementById('kloom-player');
    if (el) el.classList.remove('active');
    localStorage.removeItem(KEY);
  }

  function seek(e) {
    if (state.type === 'local_audio' && audio && audio.duration) {
      var bar = document.getElementById('kp-progress');
      if (!bar) return;
      var rect = bar.getBoundingClientRect();
      audio.currentTime = ((e.clientX - rect.left) / rect.width) * audio.duration;
    } else if (state.type === 'embed' && widget) {
      widget.getDuration().then(function(duration) {
        var bar = document.getElementById('kp-progress');
        if (!bar) return;
        var rect = bar.getBoundingClientRect();
        var seekTime = ((e.clientX - rect.left) / rect.width) * duration;
        widget.seek(seekTime);
      });
    } else if (state.type === 'youtube' && ytPlayer && ytReady) {
      var duration = ytPlayer.getDuration();
      var bar = document.getElementById('kp-progress');
      if (!bar || !duration) return;
      var rect = bar.getBoundingClientRect();
      var seekTime = ((e.clientX - rect.left) / rect.width) * duration;
      ytPlayer.seekTo(seekTime, true);
    }
  }

  /* ── private: cleanup ────────────────────────────── */

  function killAll() {
    if (audio) { audio.pause(); audio = null; }
    if (widget) { widget = null; }
    if (ytPlayer) { ytPlayer = null; ytReady = false; }
    // Remove any existing iframe
    var mid = document.getElementById('kp-mid');
    if (mid) mid.innerHTML = '';
  }

  /* ── private: local audio ────────────────────────── */

  function tickLocalAudio() {
    if (!audio || !state) return;
    state.time = audio.currentTime;
    var fill = document.getElementById('kp-fill');
    var time = document.getElementById('kp-time');
    if (fill && audio.duration)
      fill.style.width = (audio.currentTime / audio.duration * 100) + '%';
    if (time)
      time.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration);
  }

  function renderLocalAudio() {
    var el = document.getElementById('kloom-player');
    if (!el) return;
    el.classList.add('active');
    document.getElementById('kp-title').textContent = state.title;
    document.getElementById('kp-meta').textContent = state.series + ' // ' + state.date;

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

  /* ── private: Mixcloud ───────────────────────────── */

  function renderMixcloud(seekTo) {
    var el = document.getElementById('kloom-player');
    if (!el) return;
    el.classList.add('active');
    document.getElementById('kp-title').textContent = state.title;
    document.getElementById('kp-meta').textContent = state.series + ' // ' + state.date;

    var btn = document.getElementById('kp-play-btn');
    if (btn) btn.style.display = '';

    var mid = document.getElementById('kp-mid');

    // Create iframe for Mixcloud widget
    var iframeUrl = state.embed_url + '&autoplay=' + (seekTo ? '0' : '1');
    mid.innerHTML =
      '<div class="kp-embed-wrap">' +
        '<iframe id="kp-mixcloud" width="100%" height="60" src="' + iframeUrl + '" frameborder="0" allow="autoplay"></iframe>' +
        '<div class="kp-progress-wrap kp-embed-progress">' +
          '<div class="kp-progress" id="kp-progress"><div class="kp-progress-fill" id="kp-fill"></div></div>' +
          '<span class="kp-time" id="kp-time">0:00</span>' +
        '</div>' +
      '</div>';

    document.getElementById('kp-progress').addEventListener('click', seek);

    // Load Mixcloud Widget API
    loadMixcloudAPI(function() {
      var iframe = document.getElementById('kp-mixcloud');
      if (!iframe) return;
      widget = Mixcloud.PlayerWidget(iframe);
      widget.ready.then(function() {
        widget.events.play.on(function() { state.playing = true; syncBtn(); });
        widget.events.pause.on(function() { state.playing = false; syncBtn(); });
        widget.events.progress.on(function(pos, dur) {
          state.time = pos;
          var fill = document.getElementById('kp-fill');
          var time = document.getElementById('kp-time');
          if (fill && dur) fill.style.width = (pos / dur * 100) + '%';
          if (time) time.textContent = fmt(pos) + ' / ' + fmt(dur);
        });
        widget.events.ended.on(onEnded);

        if (seekTo && seekTo > 0) {
          widget.seek(seekTo);
        }
      });
    });

    syncBtn();
  }

  function loadMixcloudAPI(callback) {
    if (window.Mixcloud) { callback(); return; }
    var script = document.createElement('script');
    script.src = 'https://widget.mixcloud.com/media/js/widgetApi.js';
    script.onload = callback;
    document.head.appendChild(script);
  }

  /* ── private: YouTube ────────────────────────────── */

  function renderYouTube(seekTo) {
    var el = document.getElementById('kloom-player');
    if (!el) return;
    el.classList.add('active');
    document.getElementById('kp-title').textContent = state.title;
    document.getElementById('kp-meta').textContent = state.series + ' // ' + state.date;

    var btn = document.getElementById('kp-play-btn');
    if (btn) btn.style.display = '';

    var mid = document.getElementById('kp-mid');

    // Extract video ID from embed URL
    var videoId = extractYouTubeId(state.embed_url);

    mid.innerHTML =
      '<div class="kp-embed-wrap kp-youtube-wrap">' +
        '<div id="kp-youtube"></div>' +
        '<div class="kp-progress-wrap kp-embed-progress">' +
          '<div class="kp-progress" id="kp-progress"><div class="kp-progress-fill" id="kp-fill"></div></div>' +
          '<span class="kp-time" id="kp-time">0:00</span>' +
        '</div>' +
      '</div>';

    document.getElementById('kp-progress').addEventListener('click', seek);

    ytPendingSeek = seekTo || null;

    // Load YouTube IFrame API
    loadYouTubeAPI(function() {
      ytPlayer = new YT.Player('kp-youtube', {
        height: '60',
        width: '100%',
        videoId: videoId,
        playerVars: {
          autoplay: seekTo ? 0 : 1,
          controls: 0,
          modestbranding: 1,
          rel: 0,
          showinfo: 0
        },
        events: {
          onReady: onYTReady,
          onStateChange: onYTStateChange
        }
      });
    });

    syncBtn();
  }

  function loadYouTubeAPI(callback) {
    if (window.YT && window.YT.Player) { callback(); return; }
    window.onYouTubeIframeAPIReady = callback;
    var script = document.createElement('script');
    script.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(script);
  }

  function extractYouTubeId(url) {
    // Handle embed URLs like https://www.youtube.com/embed/VIDEO_ID
    var match = url.match(/embed\/([a-zA-Z0-9_-]+)/);
    if (match) return match[1];
    // Handle watch URLs
    match = url.match(/[?&]v=([a-zA-Z0-9_-]+)/);
    if (match) return match[1];
    return url;
  }

  function onYTReady() {
    ytReady = true;
    if (ytPendingSeek && ytPendingSeek > 0) {
      ytPlayer.seekTo(ytPendingSeek, true);
      ytPendingSeek = null;
    }
    // Start progress tracking
    setInterval(tickYouTube, 1000);
  }

  function onYTStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING) {
      state.playing = true;
      syncBtn();
    } else if (event.data === YT.PlayerState.PAUSED) {
      state.playing = false;
      syncBtn();
    } else if (event.data === YT.PlayerState.ENDED) {
      onEnded();
    }
  }

  function tickYouTube() {
    if (!ytPlayer || !ytReady || !state || state.type !== 'youtube') return;
    try {
      var currentTime = ytPlayer.getCurrentTime();
      var duration = ytPlayer.getDuration();
      state.time = currentTime;
      var fill = document.getElementById('kp-fill');
      var time = document.getElementById('kp-time');
      if (fill && duration) fill.style.width = (currentTime / duration * 100) + '%';
      if (time) time.textContent = fmt(currentTime) + ' / ' + fmt(duration);
    } catch (e) { /* player not ready */ }
  }

  /* ── private: common ─────────────────────────────── */

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

  function showResumeHint() {
    var mid = document.getElementById('kp-mid');
    if (mid) {
      var existing = document.getElementById('kp-resume');
      if (existing) return;
      var hint = document.createElement('div');
      hint.id = 'kp-resume';
      hint.className = 'kp-resume';
      hint.textContent = '\u25B6  TAP TO RESUME';
      hint.style.position = 'absolute';
      hint.style.top = '0';
      hint.style.left = '0';
      hint.style.right = '0';
      hint.style.bottom = '0';
      hint.style.display = 'flex';
      hint.style.alignItems = 'center';
      hint.style.justifyContent = 'center';
      hint.style.background = 'rgba(0,0,0,0.8)';
      hint.style.zIndex = '10';
      hint.style.cursor = 'pointer';
      hint.onclick = function() {
        hint.remove();
        togglePlay();
      };
      mid.style.position = 'relative';
      mid.appendChild(hint);
    }
  }

  /* auto-persist every 3s while playing */
  setInterval(function () {
    if (state && state.playing) persist();
  }, 3000);

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
      var id = card.id.replace('card-', '');
      var show = shows.find(function (s) { return s.id === id; });
      if (!show) { card.style.display = 'none'; return; }
      var haystack = [show.title, show.description, show.series, show.guest || '', show.tags.join(' ')].join(' ').toLowerCase();
      card.style.display = haystack.indexOf(q) !== -1 ? '' : 'none';
    });
  });
})();
