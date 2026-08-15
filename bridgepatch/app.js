(() => {
  const cfg = window.BRIDGEPATCH_CONFIG || {};

  document.querySelectorAll('[data-config-link]').forEach((node) => {
    const key = node.getAttribute('data-config-link');
    const value = cfg[key];
    if (typeof value === 'string' && value.trim()) {
      node.setAttribute('href', value);
    } else {
      node.setAttribute('aria-disabled', 'true');
      node.addEventListener('click', (event) => event.preventDefault());
    }
  });

  document.querySelectorAll('[data-config-text]').forEach((node) => {
    const key = node.getAttribute('data-config-text');
    const value = cfg[key];
    if (typeof value === 'string' && value.trim()) node.textContent = value;
  });

  document.querySelectorAll('[data-year]').forEach((node) => {
    node.textContent = String(new Date().getFullYear());
  });
})();
