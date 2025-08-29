(function(){
  function copyToClipboard(text){
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function(resolve, reject){
      try {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'absolute';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        resolve();
      } catch (e) { reject(e); }
    });
  }

  function handleShareClick(ev){
    ev.preventDefault();
    var el = ev.currentTarget;
    var title = el.getAttribute('data-title') || document.title;
    var text = el.getAttribute('data-text') || '';
    var url = el.getAttribute('data-url') || window.location.href;

    if (navigator.share) {
      navigator.share({ title: title, text: text, url: url })
        .catch(function(err){
          // Si el usuario cancela, no mostrar error.
          if (err && err.name !== 'AbortError') {
            console.warn('Error al compartir', err);
          }
        });
    } else {
      copyToClipboard(url)
        .then(function(){ alert('Enlace copiado al portapapeles'); })
        .catch(function(){ window.prompt('Copia el enlace:', url); });
    }
  }

  function init(){
    var buttons = document.querySelectorAll('.btn-share');
    buttons.forEach(function(btn){
      btn.addEventListener('click', handleShareClick);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
