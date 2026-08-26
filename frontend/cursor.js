/**
 * Cricket Companion — Simple, Instant Theme-Aware Custom Cursor
 * 0-lag hardware-accelerated tracking with theme responsive colors
 */
(function () {
  'use strict';

  // Create lightweight cursor elements
  const cursor = document.createElement('div');
  cursor.id = 'cc-cursor';

  const ring = document.createElement('div');
  ring.id = 'cc-cursor-ring';

  document.body.appendChild(ring);
  document.body.appendChild(cursor);

  // Direct, instant mouse tracking without artificial LERP delay
  document.addEventListener('mousemove', (e) => {
    const x = e.clientX;
    const y = e.clientY;
    cursor.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    ring.style.transform = `translate3d(${x}px, ${y}px, 0)`;
  }, { passive: true });

  // Click animation
  document.addEventListener('mousedown', () => {
    cursor.classList.add('cc-click');
    ring.classList.add('cc-click');
  });

  document.addEventListener('mouseup', () => {
    cursor.classList.remove('cc-click');
    ring.classList.remove('cc-click');
  });

  // Hover detection on interactive elements
  const interactiveSelectors = [
    'a', 'button', 'input', 'select', 'textarea', '.nav-item', '.btn',
    '.card', '.feature-card', '.analytics-card', '.logout-btn', '.close',
    '.heatmap-cell', 'label', '[role="button"]'
  ].join(', ');

  document.addEventListener('mouseover', (e) => {
    if (e.target.closest(interactiveSelectors)) {
      cursor.classList.add('cc-hover');
      ring.classList.add('cc-hover');
    }
  });

  document.addEventListener('mouseout', (e) => {
    if (e.target.closest(interactiveSelectors)) {
      cursor.classList.remove('cc-hover');
      ring.classList.remove('cc-hover');
    }
  });

  // Handle window focus / leave
  document.addEventListener('mouseleave', () => {
    cursor.style.opacity = '0';
    ring.style.opacity = '0';
  });

  document.addEventListener('mouseenter', () => {
    cursor.style.opacity = '1';
    ring.style.opacity = '1';
  });

  // Theme-aware styles using CSS variables
  const style = document.createElement('style');
  style.textContent = `
    *, *::before, *::after {
      cursor: none !important;
    }

    #cc-cursor {
      position: fixed;
      top: -4px;
      left: -4px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
      pointer-events: none;
      z-index: 99999;
      will-change: transform;
      transition: opacity 0.15s ease, width 0.15s ease, height 0.15s ease, background-color 0.15s ease, top 0.15s ease, left 0.15s ease;
      box-shadow: 0 0 10px var(--green-glow);
    }

    #cc-cursor-ring {
      position: fixed;
      top: -16px;
      left: -16px;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      border: 1.5px solid var(--green);
      opacity: 0.6;
      pointer-events: none;
      z-index: 99998;
      will-change: transform;
      transition: opacity 0.15s ease, width 0.2s ease, height 0.2s ease, border-color 0.2s ease, top 0.2s ease, left 0.2s ease;
    }

    #cc-cursor.cc-hover {
      background: var(--gold);
      box-shadow: 0 0 12px var(--gold-glow);
      width: 10px;
      height: 10px;
      top: -5px;
      left: -5px;
    }

    #cc-cursor-ring.cc-hover {
      width: 44px;
      height: 44px;
      top: -22px;
      left: -22px;
      border-color: var(--gold);
      opacity: 0.85;
    }

    #cc-cursor.cc-click {
      transform: scale(0.7);
    }

    #cc-cursor-ring.cc-click {
      width: 24px;
      height: 24px;
      top: -12px;
      left: -12px;
      border-color: var(--green);
      opacity: 1;
    }
  `;
  document.head.appendChild(style);
})();
