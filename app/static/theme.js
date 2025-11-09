(function(){
  const KEY = 'vocabapp-theme';
  const root = document.documentElement;

  function systemPrefersDark(){
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function current(){
    return root.getAttribute('data-theme') || (systemPrefersDark() ? 'dark' : 'light');
  }

  function apply(theme){
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem(KEY, theme); } catch(_){}
    updateButton(theme);
  }

  function load(){
    try {
      const saved = localStorage.getItem(KEY);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch(_){}
    return systemPrefersDark() ? 'dark' : 'light';
  }

  function toggle(){
    const next = current() === 'dark' ? 'light' : 'dark';
    apply(next);
  }

  function updateButton(theme){
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.setAttribute('aria-label', theme === 'dark' ? 'Chuyển sang nền sáng' : 'Chuyển sang nền tối');
    // Use moon and sun icons that work well with gradient background
    btn.innerHTML = theme === 'dark' ? '🌙' : '☀️';
    // Update button appearance based on theme
    if (theme === 'dark') {
      btn.classList.add('dark-mode');
    } else {
      btn.classList.remove('dark-mode');
    }
  }

  function ensureButton(){
    if (document.getElementById('theme-toggle')) return;
    const btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.className = 'theme-toggle';
    btn.style.position = 'fixed';
    btn.style.right = '16px';
    btn.style.bottom = '16px';
    btn.style.zIndex = '1000';
    btn.type = 'button';
    btn.addEventListener('click', toggle);
    document.body.appendChild(btn);
    updateButton(current());
  }

  // Initialize ASAP
  const initial = load();
  apply(initial);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureButton);
  } else {
    ensureButton();
  }

  // React to system changes if user hasn't explicitly chosen
  try {
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    mql.addEventListener('change', (e)=>{
      const saved = localStorage.getItem(KEY);
      if (!saved) apply(e.matches ? 'dark' : 'light');
    });
  } catch(_){}
})();
