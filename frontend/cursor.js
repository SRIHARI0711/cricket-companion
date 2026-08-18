/**
 * Cricket Companion — Custom Cursor
 * A cricket-ball cursor with trailing dot effect and magnetic hover
 */
(function () {
  'use strict';

  /* ---- Create DOM elements ---- */
  const cursor = document.createElement('div');
  cursor.id = 'cc-cursor';
  cursor.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22">
      <circle cx="12" cy="12" r="11" fill="#c0392b" stroke="#922b21" stroke-width="0.5"/>
      <path d="M12 1 C12 1, 7 5, 7 12 C7 19, 12 23, 12 23" stroke="#f5f5f5" stroke-width="0.8" fill="none" stroke-linecap="round"/>
      <path d="M12 1 C12 1, 17 5, 17 12 C17 19, 12 23, 12 23" stroke="#f5f5f5" stroke-width="0.8" fill="none" stroke-linecap="round"/>
      <path d="M1 12 C1 12, 5 7, 12 7 C19 7, 23 12, 23 12" stroke="#f5f5f5" stroke-width="0.8" fill="none" stroke-linecap="round"/>
      <path d="M1 12 C1 12, 5 17, 12 17 C19 17, 23 12, 23 12" stroke="#f5f5f5" stroke-width="0.8" fill="none" stroke-linecap="round"/>
      <circle cx="12" cy="12" r="2" fill="rgba(255,255,255,0.15)"/>
    </svg>`;

  const ring = document.createElement('div');
  ring.id = 'cc-cursor-ring';

  /* Trail dots */
  const TRAIL_COUNT = 8;
  const trail = [];
  for (let i = 0; i < TRAIL_COUNT; i++) {
    const dot = document.createElement('div');
    dot.className = 'cc-trail-dot';
    dot.style.opacity = ((TRAIL_COUNT - i) / TRAIL_COUNT * 0.5).toString();
    dot.style.width = dot.style.height = `${Math.max(3, 8 - i)}px`;
    document.body.appendChild(dot);
    trail.push({ el: dot, x: -100, y: -100 });
  }

  document.body.appendChild(ring);
  document.body.appendChild(cursor);

  /* ---- State ---- */
  let mouseX = -200, mouseY = -200;
  let cursorX = -200, cursorY = -200;
  let ringX = -200, ringY = -200;
  let isHovering = false;
  let isClicking = false;

  /* ---- Mouse tracking ---- */
  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  document.addEventListener('mousedown', () => {
    isClicking = true;
    cursor.classList.add('cc-cursor--click');
    ring.classList.add('cc-ring--click');
  });

  document.addEventListener('mouseup', () => {
    isClicking = false;
    cursor.classList.remove('cc-cursor--click');
    ring.classList.remove('cc-ring--click');
  });

  /* ---- Hover detection on interactive elements ---- */
  const interactiveSelectors = [
    'a', 'button', '[role="button"]', 'input', 'select', 'textarea',
    '.nav-item', '.btn', '.feature-card', '.card', 'th', '.logout-btn',
    '.close', '.heatmap-cell', 'label[for]', '.login-btn'
  ].join(', ');

  document.addEventListener('mouseover', (e) => {
    if (e.target.closest(interactiveSelectors)) {
      isHovering = true;
      cursor.classList.add('cc-cursor--hover');
      ring.classList.add('cc-ring--hover');
    }
  });

  document.addEventListener('mouseout', (e) => {
    if (e.target.closest(interactiveSelectors)) {
      isHovering = false;
      cursor.classList.remove('cc-cursor--hover');
      ring.classList.remove('cc-ring--hover');
    }
  });

  /* ---- Animation loop ---- */
  const LERP_CURSOR = 0.18;
  const LERP_RING = 0.08;
  const TRAIL_LERP_BASE = 0.22;

  let prevTrailPositions = trail.map(() => ({ x: -200, y: -200 }));

  function animate() {
    /* Smooth cursor follow */
    cursorX += (mouseX - cursorX) * LERP_CURSOR;
    cursorY += (mouseY - cursorY) * LERP_CURSOR;

    /* Ring lags more for elastic feel */
    ringX += (mouseX - ringX) * LERP_RING;
    ringY += (mouseY - ringY) * LERP_RING;

    cursor.style.transform = `translate(${cursorX - 11}px, ${cursorY - 11}px)`;
    ring.style.transform   = `translate(${ringX - 20}px, ${ringY - 20}px)`;

    /* Trail dots follow each other */
    let prevX = cursorX, prevY = cursorY;
    for (let i = 0; i < trail.length; i++) {
      const t = trail[i];
      const lerpFactor = TRAIL_LERP_BASE - i * 0.018;
      t.x += (prevX - t.x) * Math.max(0.05, lerpFactor);
      t.y += (prevY - t.y) * Math.max(0.05, lerpFactor);
      const size = parseInt(t.el.style.width);
      t.el.style.transform = `translate(${t.x - size / 2}px, ${t.y - size / 2}px)`;
      prevX = t.x;
      prevY = t.y;
    }

    requestAnimationFrame(animate);
  }

  /* ---- Hide on mouse leave, show on enter ---- */
  document.addEventListener('mouseleave', () => {
    cursor.style.opacity = '0';
    ring.style.opacity = '0';
    trail.forEach(t => { t.el.style.opacity = '0'; });
  });

  document.addEventListener('mouseenter', () => {
    cursor.style.opacity = '1';
    ring.style.opacity = '1';
    trail.forEach((t, i) => {
      t.el.style.opacity = ((TRAIL_COUNT - i) / TRAIL_COUNT * 0.5).toString();
    });
  });

  /* ---- Inject CSS ---- */
  const style = document.createElement('style');
  style.textContent = `
    *, *::before, *::after { cursor: none !important; }

    #cc-cursor {
      position: fixed;
      top: 0; left: 0;
      width: 22px; height: 22px;
      pointer-events: none;
      z-index: 99999;
      will-change: transform;
      transition: opacity 0.2s, transform 0.05s;
      filter: drop-shadow(0 0 6px rgba(192,57,43,0.7));
    }

    #cc-cursor.cc-cursor--hover {
      filter: drop-shadow(0 0 12px rgba(0,200,150,0.9));
      transform-origin: center;
    }

    #cc-cursor.cc-cursor--click {
      filter: drop-shadow(0 0 18px rgba(240,165,0,1));
    }

    #cc-cursor--hover svg circle:first-child { fill: #00c896; }

    #cc-cursor-ring {
      position: fixed;
      top: 0; left: 0;
      width: 40px; height: 40px;
      border-radius: 50%;
      border: 1.5px solid rgba(0,200,150,0.5);
      pointer-events: none;
      z-index: 99998;
      will-change: transform;
      transition: opacity 0.2s, width 0.25s ease, height 0.25s ease, border-color 0.25s;
    }

    #cc-cursor-ring.cc-ring--hover {
      width: 56px;
      height: 56px;
      border-color: rgba(0,200,150,0.8);
      transform-origin: center;
      /* compensate for size change so it stays centered */
      margin: -8px;
    }

    #cc-cursor-ring.cc-ring--click {
      border-color: rgba(240,165,0,0.9);
      width: 32px;
      height: 32px;
      margin: 4px;
    }

    .cc-trail-dot {
      position: fixed;
      top: 0; left: 0;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(0,200,150,0.8), rgba(0,200,150,0));
      pointer-events: none;
      z-index: 99997;
      will-change: transform;
      transition: opacity 0.3s;
    }
  `;
  document.head.appendChild(style);

  /* Start loop after DOM is ready */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', animate);
  } else {
    animate();
  }
})();
