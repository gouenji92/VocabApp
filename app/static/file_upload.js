// Reusable drag & drop + paste handler for .custum-file-upload components
// Attaches events to any label.custum-file-upload that directly contains an <input type="file">.
(function(){
  function enhance(container){
    if(container.__enhanced) return; // avoid duplicate
    const input = container.querySelector('input[type=file]');
    if(!input) return;
    container.__enhanced = true;

    const textSpan = container.querySelector('.text span');
    const originalText = textSpan ? textSpan.textContent : '';

    function setHover(on){
      if(on) container.classList.add('drag-active');
      else container.classList.remove('drag-active');
    }
    function setFiles(fileList){
      if(!fileList || !fileList.length) return;
      // Assign file list to input (only possible via DataTransfer)
      const dt = new DataTransfer();
      for(const f of fileList){ dt.items.add(f); }
      input.files = dt.files;
      if(textSpan){
        if(fileList.length === 1){ textSpan.textContent = 'Đã chọn: ' + fileList[0].name; }
        else { textSpan.textContent = fileList.length + ' files selected'; }
      }
    }

    // Drag events
    ['dragenter','dragover'].forEach(evtName => {
      container.addEventListener(evtName, e => { e.preventDefault(); e.stopPropagation(); setHover(true); });
    });
    ['dragleave','dragend','drop'].forEach(evtName => {
      container.addEventListener(evtName, e => { e.preventDefault(); e.stopPropagation(); setHover(false); });
    });
    container.addEventListener('drop', e => {
      if(e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length){
        setFiles(e.dataTransfer.files);
      }
    });

    // Paste support (for images only realistically)
    container.addEventListener('paste', e => {
      if(!(e.clipboardData && e.clipboardData.items)) return;
      const items = Array.from(e.clipboardData.items).filter(it => it.kind === 'file');
      if(!items.length) return;
      const files = items.map(it => it.getAsFile()).filter(Boolean);
      if(files.length){ setFiles(files); }
    });

    // Keyboard accessibility: focus -> show outline
    container.setAttribute('tabindex','0');
    container.addEventListener('focus', () => container.classList.add('upload-focus'));
    container.addEventListener('blur', () => container.classList.remove('upload-focus'));

    // Reset text on form reset
    const form = container.closest('form');
    if(form){
      form.addEventListener('reset', () => { if(textSpan) textSpan.textContent = originalText; });
    }
  }

  function init(){
    document.querySelectorAll('label.custum-file-upload').forEach(enhance);
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
