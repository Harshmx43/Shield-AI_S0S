// ── ShieldAI Global Socket Connection ────────────────────────────────────────

const shieldSocket = io(window.location.origin, {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionAttempts: 5
});

shieldSocket.on('connect', () => {
  console.log('ShieldAI socket connected');
  // If on dashboard, join authority room
  if (window.location.pathname.includes('dashboard')) {
    shieldSocket.emit('join_dashboard');
  }
});

shieldSocket.on('disconnect', () => {
  console.log('ShieldAI socket disconnected');
});

shieldSocket.on('connect_error', (err) => {
  console.error('Socket error:', err);
});
