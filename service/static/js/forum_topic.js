/* ===== forum_topic.js ===== */

document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Голосование ---------- */
  function applyVote(likeBtn, dislikeBtn, votedType) {
    const dim = function (btn) {
      btn.dataset.voted = 'true';
      btn.style.opacity = '0.4';
      btn.style.cursor = 'not-allowed';
      btn.style.filter = 'grayscale(100%)';
    };
    if (votedType === 'like')    { likeBtn.dataset.voted = 'true'; dim(dislikeBtn); }
    if (votedType === 'dislike') { dislikeBtn.dataset.voted = 'true'; dim(likeBtn); }
  }

  document.querySelectorAll('.message-rating').forEach(function (rating) {
    const likeBtn    = rating.querySelector('.like-btn');
    const dislikeBtn = rating.querySelector('.dislike-btn');

    if (likeBtn.dataset.voted && likeBtn.dataset.voted !== '') {
      applyVote(likeBtn, dislikeBtn, likeBtn.dataset.voted);
    }

    async function sendRate(btn, ratingType, messageAddr, topicAddr) {
      if (['true', 'like', 'dislike'].includes(likeBtn.dataset.voted)) return;
      try {
        const resp = await fetch('/forum/topic/' + topicAddr + '/message/' + messageAddr + '/rate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'rating_type=' + ratingType
        });
        const data = await resp.json();
        if (resp.ok && data.status === 'ok') {
          const span = btn.querySelector(ratingType === 'like' ? '.like-count' : '.dislike-count');
          span.textContent = parseInt(span.textContent) + 1;
          applyVote(likeBtn, dislikeBtn, ratingType);
        }
      } catch (e) {
        console.error('Ошибка голосования:', e);
      }
    }

    likeBtn.addEventListener('click', function () {
      sendRate(likeBtn, 'like', likeBtn.dataset.message, likeBtn.dataset.topic);
    });
    dislikeBtn.addEventListener('click', function () {
      sendRate(dislikeBtn, 'dislike', dislikeBtn.dataset.message, dislikeBtn.dataset.topic);
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeLightbox();
  });

});


/* ---------- Автодополнение ---------- */
(function () {
  function buildTopicDict(messages, topicMeta) {
    const freq = {};
    messages.forEach(function (text) {
      const words = text.match(/[а-яёА-ЯЁa-zA-Z]{3,}/g) || [];
      words.forEach(function (w) {
        const k = w.toLowerCase();
        freq[k] = (freq[k] || 0) + 10;
      });
    });
    (topicMeta.match(/[а-яёА-ЯЁa-zA-Z]{3,}/g) || []).forEach(function (w) {
      const k = w.toLowerCase();
      freq[k] = (freq[k] || 0) + 5;
    });
    return Object.entries(freq)
      .sort(function (a, b) { return b[1] - a[1]; })
      .map(function (e) { return e[0]; });
  }

  function getCurrentWord(text, pos) {
    const m = text.slice(0, pos).match(/[а-яёА-ЯЁa-zA-Z]+$/);
    return m ? m[0] : '';
  }

  function getSuggestion(word, wordList) {
    if (word.length < 2) return '';
    const lower = word.toLowerCase();
    const match = wordList.find(function (w) { return w.startsWith(lower) && w !== lower; });
    if (!match) return '';
    if (word[0] === word[0].toUpperCase() && word[0] !== word[0].toLowerCase()) {
      return match[0].toUpperCase() + match.slice(1);
    }
    return match;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/ /g, '&nbsp;').replace(/\n/g, '<br>');
  }

  window.initAutocomplete = function (topicMessages, topicMeta) {
    const textarea = document.getElementById('messageInput');
    const ghost    = document.getElementById('ghost');
    if (!textarea || !ghost) return;

    const topicWords  = buildTopicDict(topicMessages, topicMeta);
    const topicSet    = new Set(topicWords);
    const globalWords = (typeof RU_WORDS !== 'undefined') ? RU_WORDS : [];
    const WORDS = topicWords.concat(globalWords.filter(function (w) { return !topicSet.has(w); }));

    let currentSuggestion = '';
    let currentWordStart  = 0;

    function syncGhostStyles() {
      const cs = window.getComputedStyle(textarea);
      ['paddingTop','paddingBottom','paddingLeft','paddingRight',
       'fontSize','fontFamily','fontWeight','lineHeight','letterSpacing',
       'borderRadius','borderTopWidth','borderBottomWidth',
       'borderLeftWidth','borderRightWidth','boxSizing','wordWrap','whiteSpace'
      ].forEach(function (p) { ghost.style[p] = cs[p]; });
      ghost.style.width  = textarea.offsetWidth  + 'px';
      ghost.style.height = textarea.offsetHeight + 'px';
    }

    function updateGhost() {
      const text   = textarea.value;
      const cursor = textarea.selectionStart;
      const word   = getCurrentWord(text, cursor);
      currentWordStart  = cursor - word.length;
      currentSuggestion = getSuggestion(word, WORDS);
      if (currentSuggestion && word) {
        const tail = currentSuggestion.slice(word.length);
        ghost.innerHTML = escapeHtml(text.slice(0, cursor)) +
          '<span class="autocomplete-ghost-suggestion">' + escapeHtml(tail) + '</span>' +
          escapeHtml(text.slice(cursor));
      } else {
        ghost.innerHTML = escapeHtml(text);
      }
      ghost.scrollTop = textarea.scrollTop;
    }

    textarea.addEventListener('keydown', function (e) {
      if (e.key === 'Tab' && currentSuggestion) {
        e.preventDefault();
        const text    = textarea.value;
        const cursor  = textarea.selectionStart;
        const newText = text.slice(0, currentWordStart) + currentSuggestion + text.slice(cursor);
        textarea.value = newText;
        const nc = currentWordStart + currentSuggestion.length;
        textarea.setSelectionRange(nc, nc);
        currentSuggestion = '';
        ghost.innerHTML   = escapeHtml(newText);
      }
      if (e.key === 'Escape') {
        currentSuggestion = '';
        ghost.innerHTML   = escapeHtml(textarea.value);
      }
    });

    textarea.addEventListener('input',  updateGhost);
    textarea.addEventListener('keyup',  updateGhost);
    textarea.addEventListener('click',  updateGhost);
    textarea.addEventListener('scroll', function () { ghost.scrollTop = textarea.scrollTop; });
    window.addEventListener('load',   function () { syncGhostStyles(); updateGhost(); });
    window.addEventListener('resize', function () { syncGhostStyles(); updateGhost(); });
  };
})();


/* ---------- Прикрепление фото ---------- */
function handlePhotoSelect(input) {
  if (!input.files || !input.files[0]) return;
  const reader = new FileReader();
  reader.onload = function (e) {
    document.getElementById('previewImg').src = e.target.result;
    document.getElementById('attachThumb').classList.add('visible');
    document.getElementById('attachBtn').classList.add('has-photo');
    document.getElementById('messageInput').style.paddingLeft = '76px';
  };
  reader.readAsDataURL(input.files[0]);
}

function removePhoto() {
  document.getElementById('imageInput').value  = '';
  document.getElementById('previewImg').src    = '';
  document.getElementById('attachThumb').classList.remove('visible');
  document.getElementById('attachBtn').classList.remove('has-photo');
  document.getElementById('messageInput').style.paddingLeft = '';
}


/* ---------- Лайтбокс ---------- */
function openLightbox(src) {
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox').classList.add('active');
}

function closeLightbox() {
  document.getElementById('lightbox').classList.remove('active');
  document.getElementById('lightbox-img').src = '';
}


/* ---------- Удаление ---------- */
async function deleteMessage(btn) {
  const actionsDiv  = btn.closest('.message-actions');
  const messageAddr = actionsDiv.dataset.addr;

  if (!confirm('Удалить сообщение?')) return;
  btn.disabled = true;

  try {
    const resp = await fetch('/api/forum/delete_message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message_addr: messageAddr })
    });
    const data = await resp.json();
    if (data.success) {
      const card = document.getElementById('message-' + messageAddr);
      if (card) card.remove();
    } else {
      btn.disabled = false;
      alert('Ошибка удаления: ' + (data.message || 'неизвестная ошибка'));
    }
  } catch (e) {
    btn.disabled = false;
    alert('Ошибка сети');
  }
}


/* ---------- Редактирование ---------- */
function startEdit(btn) {
  const actionsDiv  = btn.closest('.message-actions');
  const messageAddr = actionsDiv.dataset.addr;
  const currentText = actionsDiv.dataset.content;
  const card        = document.getElementById('message-' + messageAddr);
  const textDiv     = card.querySelector('.message-text');

  if (card.querySelector('.edit-textarea')) return;

  const textarea = document.createElement('textarea');
  textarea.className     = 'edit-textarea form-control';
  textarea.rows          = 4;
  textarea.value         = currentText;
  textarea.style.cssText = 'width:100%;margin-bottom:8px;display:block;box-sizing:border-box;';

  const editActions = document.createElement('div');
  editActions.className = 'edit-actions';
  editActions.style.cssText = 'display:flex;gap:8px;margin-bottom:8px;';

  const saveBtn = document.createElement('button');
  saveBtn.textContent = 'Сохранить';
  saveBtn.className   = 'btn-primary';
  saveBtn.type        = 'button';

  const cancelBtn = document.createElement('button');
  cancelBtn.textContent = 'Отмена';
  cancelBtn.className   = 'btn-secondary';
  cancelBtn.type        = 'button';

  editActions.appendChild(saveBtn);
  editActions.appendChild(cancelBtn);

  function closeEdit() {
    textarea.remove();
    editActions.remove();
    textDiv.style.display    = '';
    actionsDiv.style.display = '';
  }

  cancelBtn.onclick = closeEdit;

  saveBtn.onclick = async function () {
    const newText = textarea.value.trim();
    if (!newText) { alert('Сообщение не может быть пустым'); return; }
    saveBtn.disabled = cancelBtn.disabled = true;
    try {
      const resp = await fetch('/api/forum/edit_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_addr: messageAddr, new_text: newText })
      });
      const data = await resp.json();
      if (data.success) {
        textDiv.textContent = newText;
        actionsDiv.dataset.content = newText;
        closeEdit();
      } else {
        saveBtn.disabled = cancelBtn.disabled = false;
        alert('Ошибка: ' + (data.message || 'неизвестная ошибка'));
      }
    } catch (e) {
      saveBtn.disabled = cancelBtn.disabled = false;
      alert('Ошибка сети');
    }
  };

  textDiv.style.display    = 'none';
  actionsDiv.style.display = 'none';
  actionsDiv.after(textarea, editActions);
}