// Feed Interactions JavaScript
let currentPage = 1;
let isLoading = false;
let hasMore = true;
let selectedImageFile = null;

// ========== Image Upload Functions ==========
function setupImageDragDrop() {
  const dropZone = document.getElementById('imageDropZone');
  if (!dropZone) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', handleDrop);
}

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  if (files.length > 0) {
    handleImageFile(files[0]);
  }
}

function previewImage(event) {
  const file = event.target.files[0];
  if (file) {
    handleImageFile(file);
  }
}

function handleImageFile(file) {
  // Validate file type
  if (!file.type.startsWith('image/')) {
    window.toast.show('Vui lòng chọn file ảnh', 'warning');
    return;
  }

  // Validate file size (max 5MB)
  if (file.size > 5 * 1024 * 1024) {
    window.toast.show('Ảnh không được vượt quá 5MB', 'warning');
    return;
  }

  selectedImageFile = file;

  // Preview
  const reader = new FileReader();
  reader.onload = function(e) {
    const preview = document.getElementById('imagePreview');
    const container = document.getElementById('imagePreviewContainer');
    const dropZone = document.getElementById('imageDropZone');
    
    preview.src = e.target.result;
    container.classList.add('active');
    dropZone.style.display = 'none';
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  selectedImageFile = null;
  const preview = document.getElementById('imagePreview');
  const container = document.getElementById('imagePreviewContainer');
  const dropZone = document.getElementById('imageDropZone');
  const fileInput = document.getElementById('imageInput');
  
  preview.src = '';
  container.classList.remove('active');
  dropZone.style.display = 'block';
  fileInput.value = '';
}

// ========== Modal Functions ==========
function openCreatePostModal() {
  document.getElementById('createPostModal').classList.add('active');
  document.getElementById('postContent').focus();
  setupImageDragDrop();
}

function closeCreatePostModal() {
  document.getElementById('createPostModal').classList.remove('active');
  document.getElementById('postContent').value = '';
  document.getElementById('attachedSetId').value = '';
  removeImage();
}

async function submitPost() {
  const content = document.getElementById('postContent').value.trim();
  const attachedSetId = document.getElementById('attachedSetId').value;
  const btn = document.getElementById('btnSubmitPost');
  
  if (!content && !selectedImageFile) {
    window.toast.show('Vui lòng nhập nội dung hoặc thêm ảnh', 'warning');
    return;
  }
  
  btn.disabled = true;
  btn.textContent = 'Đang đăng...';
  
  try {
    let imageUrl = null;
    
    // Upload image first if exists
    if (selectedImageFile) {
      const formData = new FormData();
      formData.append('file', selectedImageFile);
      
      const uploadResponse = await fetch('/api/upload/image', {
        method: 'POST',
        body: formData
      });
      
      if (uploadResponse.ok) {
        const uploadData = await uploadResponse.json();
        imageUrl = uploadData.url;
      } else {
        throw new Error('Không thể upload ảnh');
      }
    }
    
    // Create post
    const response = await fetch('/api/posts/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        content, 
        attached_set_id: attachedSetId || null,
        image_url: imageUrl
      })
    });
    
    if (response.ok) {
      closeCreatePostModal();
      window.toast.show('Đã đăng bài thành công!', 'success');
      setTimeout(() => window.location.reload(), 1000);
    } else {
      const data = await response.json();
      window.toast.show('Lỗi: ' + (data.error || 'Không thể đăng bài'), 'error');
    }
  } catch (error) {
    window.toast.show('Lỗi: ' + error.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Đăng';
  }
}

// Close modal on outside click
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('createPostModal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeCreatePostModal();
      }
    });
  }
});

// ========== Like Functions ==========
async function toggleLike(setId, button) {
  try {
    const isLiked = button.classList.contains('liked');
    const response = await fetch(`/api/sets/${setId}/like`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ unlike: isLiked })
    });
    
    if (response.ok) {
      const data = await response.json();
      button.classList.toggle('liked');
      
      // Update icon (iconify classes)
      const icon = button.querySelector('.iconify') || button.querySelector('.icon-svg');
      if (icon) {
        if (data.liked) {
          icon.classList.remove('icon-heart');
          icon.classList.add('icon-heart-filled');
          // Fallback if using <img>
          if (icon.tagName === 'IMG') {
            icon.src = icon.src.replace('icon_heart.svg', 'icon_heart_filled.svg');
          }
        } else {
          icon.classList.remove('icon-heart-filled');
          icon.classList.add('icon-heart');
          if (icon.tagName === 'IMG') {
            icon.src = icon.src.replace('icon_heart_filled.svg', 'icon_heart.svg');
          }
        }
      }
      
      updateLikeCount(setId, data.likes_count);
      
      // Animate
      if (icon) {
        icon.style.transform = 'scale(1.3)';
        setTimeout(() => icon.style.transform = 'scale(1)', 300);
      }
    }
  } catch (error) {
    console.error('Error toggling like:', error);
  }
}

function updateLikeCount(setId, count) {
  const card = document.querySelector(`[data-set-id="${setId}"]`);
  if (!card) return;
  
  const stats = card.querySelector('.post-stats .stat-item');
  if (stats) {
    stats.innerHTML = count > 0 ? `<span class="iconify icon-heart icon-16 icon-gradient-accent" style="margin-right:4px;opacity:.85;"></span>${count}` : '';
  }
}

// ========== Bookmark Functions ==========
async function toggleBookmark(setId, button) {
  try {
    const response = await fetch(`/api/sets/${setId}/bookmark`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      const data = await response.json();
      button.classList.toggle('saved');
      
      // Update icon (iconify classes)
      const icon = button.querySelector('.iconify') || button.querySelector('.icon-svg');
      if (data.saved) {
        if (icon) {
          icon.classList.remove('icon-bookmark');
          icon.classList.add('icon-bookmark-filled');
          if (icon.tagName === 'IMG') {
            icon.src = icon.src.replace('icon_bookmark.svg', 'icon_bookmark_filled.svg');
          }
          icon.style.transform = 'scale(1.2) rotate(10deg)';
          setTimeout(() => icon.style.transform = 'scale(1) rotate(0)', 300);
        }
        window.toast.show('Đã lưu bộ từ', 'success');
      } else {
        if (icon) {
          icon.classList.remove('icon-bookmark-filled');
          icon.classList.add('icon-bookmark');
          if (icon.tagName === 'IMG') {
            icon.src = icon.src.replace('icon_bookmark_filled.svg', 'icon_bookmark.svg');
          }
          icon.style.transform = 'scale(1.2) rotate(10deg)';
          setTimeout(() => icon.style.transform = 'scale(1) rotate(0)', 300);
        }
        window.toast.show('Đã bỏ lưu', 'info');
      }
    }
  } catch (error) {
    console.error('Error toggling bookmark:', error);
  }
}

// ========== Comments Functions ==========
function toggleComments(setId) {
  const commentsSection = document.getElementById(`comments-${setId}`);
  const isActive = commentsSection.classList.contains('active');
  
  if (!isActive) {
    loadComments(setId);
  }
  commentsSection.classList.toggle('active');
}

async function loadComments(setId) {
  try {
    const response = await fetch(`/api/sets/${setId}/comments`);
    const comments = await response.json();
    const commentsList = document.getElementById(`comments-list-${setId}`);
    
    commentsList.innerHTML = comments.map(comment => renderComment(comment, setId)).join('');
  } catch (error) {
    console.error('Error loading comments:', error);
  }
}

function renderComment(comment, setId) {
  const avatarHTML = comment.user_avatar 
    ? `<img src="${comment.user_avatar}" class="comment-avatar" alt="${comment.user_display_name}" />`
    : `<div class="comment-avatar">${comment.user_display_name ? comment.user_display_name[0].toUpperCase() : 'U'}</div>`;
  
  const repliesHTML = comment.replies && comment.replies.length > 0
    ? `<div class="comment-replies">${comment.replies.map(reply => renderReply(reply)).join('')}</div>`
    : '';
  
  // Check if current user is the comment author
  const isOwner = window.currentUsername === comment.username;
  const menuHTML = isOwner ? `
    <div style="position: relative; margin-left: auto;">
      <button class="comment-menu" onclick="toggleCommentMenu(event, '${comment.id}')">
        <span class="iconify icon-more icon-16 icon-gradient-accent"></span>
      </button>
      <div class="menu-dropdown" id="comment-menu-${comment.id}">
        <button class="menu-item" onclick="editComment('${comment.id}', event)">
          <span class="iconify icon-edit icon-18 icon-gradient-accent"></span>
          <span>Chỉnh sửa</span>
        </button>
        <button class="menu-item danger" onclick="deleteComment('${comment.id}', event)">
          <span class="iconify icon-delete icon-18 icon-gradient-accent"></span>
          <span>Xóa</span>
        </button>
      </div>
    </div>
  ` : '';
  
  const editedIndicator = comment.edited_at ? '<span style="color: #65676b;"> · Đã chỉnh sửa</span>' : '';
  
  return `
    <div class="comment-item" id="comment-${comment.id}" data-comment-id="${comment.id}" style="position: relative;">
      ${avatarHTML}
      <div class="comment-content" style="flex: 1;">
        <div class="comment-bubble">
          <div class="comment-author">${comment.user_display_name || comment.username}</div>
          <div class="comment-text">${escapeHtml(comment.content)}</div>
        </div>
        <div class="comment-actions">
          <span class="comment-time">${formatTime(comment.created_at)}${editedIndicator}</span>
          <button class="comment-action-btn ${comment.is_liked ? 'liked' : ''}" onclick="toggleCommentLike('${comment.id}', this)">
            ${comment.is_liked ? '❤️' : 'Thích'} ${comment.likes_count > 0 ? comment.likes_count : ''}
          </button>
          <button class="comment-action-btn" onclick="showReplyInput('${comment.id}')">Trả lời</button>
        </div>
        ${repliesHTML}
        <div class="reply-input" id="reply-input-${comment.id}" style="display:none;">
          <input type="text" placeholder="Viết trả lời..." id="reply-text-${comment.id}" onkeypress="if(event.key==='Enter') postReply('${comment.id}')">
          <button onclick="postReply('${comment.id}')">Gửi</button>
        </div>
      </div>
      ${menuHTML}
    </div>
  `;
}

function renderReply(reply) {
  const avatarHTML = reply.user_avatar 
    ? `<img src="${reply.user_avatar}" class="comment-avatar" style="width:28px;height:28px;" alt="${reply.user_display_name}" />`
    : `<div class="comment-avatar" style="width:28px;height:28px;font-size:0.8em;">${reply.user_display_name ? reply.user_display_name[0].toUpperCase() : 'U'}</div>`;
  
  // Check if current user is the reply author
  const isOwner = window.currentUsername === reply.username;
  const menuHTML = isOwner ? `
    <div style="position: relative; margin-left: auto;">
      <button class="comment-menu" onclick="toggleReplyMenu(event, '${reply.id}')">
        <span class="iconify icon-more icon-14 icon-gradient-accent"></span>
      </button>
      <div class="menu-dropdown" id="reply-menu-${reply.id}">
        <button class="menu-item" onclick="editReply('${reply.id}', event)">
          <span class="iconify icon-edit icon-18 icon-gradient-accent"></span>
          <span>Chỉnh sửa</span>
        </button>
        <button class="menu-item danger" onclick="deleteReply('${reply.id}', event)">
          <span class="iconify icon-delete icon-18 icon-gradient-accent"></span>
          <span>Xóa</span>
        </button>
      </div>
    </div>
  ` : '';
  
  const editedIndicator = reply.edited_at ? '<span style="color: #65676b;"> · Đã chỉnh sửa</span>' : '';
  
  return `
    <div class="comment-item" id="reply-${reply.id}" style="margin-bottom:10px; position: relative;">
      ${avatarHTML}
      <div class="comment-content" style="flex: 1;">
        <div class="comment-bubble">
          <div class="comment-author">${reply.user_display_name || reply.username}</div>
          <div class="comment-text">${escapeHtml(reply.content)}</div>
        </div>
        <div class="comment-actions">
          <span class="comment-time">${formatTime(reply.created_at)}${editedIndicator}</span>
        </div>
      </div>
      ${menuHTML}
    </div>
  `;
}

function toggleCommentMenu(event, commentId) {
  event.stopPropagation();
  const menu = document.getElementById(`comment-menu-${commentId}`);
  
  // Close all other menus
  document.querySelectorAll('.menu-dropdown').forEach(m => {
    if (m.id !== `comment-menu-${commentId}`) m.classList.remove('active');
  });
  
  menu.classList.toggle('active');
}

function toggleReplyMenu(event, replyId) {
  event.stopPropagation();
  const menu = document.getElementById(`reply-menu-${replyId}`);
  
  // Close all other menus
  document.querySelectorAll('.menu-dropdown').forEach(m => {
    if (m.id !== `reply-menu-${replyId}`) m.classList.remove('active');
  });
  
  menu.classList.toggle('active');
}

async function postComment(setId) {
  const input = document.getElementById(`comment-input-${setId}`);
  const content = input.value.trim();
  
  if (!content) return;
  
  try {
    const response = await fetch(`/api/sets/${setId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    
    if (response.ok) {
      input.value = '';
      loadComments(setId);
      const data = await response.json();
      updateCommentCount(setId, data.comments_count);
    }
  } catch (error) {
    console.error('Error posting comment:', error);
  }
}

function updateCommentCount(setId, count) {
  const card = document.querySelector(`[data-set-id="${setId}"]`);
  if (!card) return;
  
  const stats = card.querySelector('.post-stats span:last-child');
  if (stats) {
    const text = count > 0 ? `${count} bình luận` : '';
    stats.innerHTML = text;
  }
}

async function toggleCommentLike(commentId, button) {
  try {
    const response = await fetch(`/api/comments/${commentId}/like`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      const data = await response.json();
      button.classList.toggle('liked');
      button.textContent = data.liked ? `❤️ ${data.likes_count || ''}` : `Thích ${data.likes_count > 0 ? data.likes_count : ''}`;
    }
  } catch (error) {
    console.error('Error toggling comment like:', error);
  }
}

function showReplyInput(commentId) {
  const replyInput = document.getElementById(`reply-input-${commentId}`);
  if (replyInput.style.display === 'none') {
    replyInput.style.display = 'flex';
    document.getElementById(`reply-text-${commentId}`).focus();
  } else {
    replyInput.style.display = 'none';
  }
}

async function postReply(commentId) {
  const input = document.getElementById(`reply-text-${commentId}`);
  const content = input.value.trim();
  
  if (!content) return;
  
  try {
    const response = await fetch(`/api/comments/${commentId}/reply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    
    if (response.ok) {
      input.value = '';
      // Reload comments to show new reply
      const commentItem = document.querySelector(`[data-comment-id="${commentId}"]`);
      const postCard = commentItem.closest('.post-card');
      const setId = postCard.getAttribute('data-set-id');
      loadComments(setId);
    }
  } catch (error) {
    console.error('Error posting reply:', error);
  }
}

// ========== Share Functions ==========
let currentShareSetId = null;
let currentShareSetName = null;

function shareSet(setId, setName) {
  currentShareSetId = setId;
  currentShareSetName = setName;
  
  // Update modal content
  const previewDiv = document.getElementById('shareSetPreview');
  previewDiv.innerHTML = `
    <h4>📚 ${escapeHtml(setName)}</h4>
    <p>Bộ từ này sẽ được chia sẻ về trang cá nhân của bạn</p>
  `;
  
  // Clear previous caption
  document.getElementById('shareCaption').value = '';
  
  // Show modal
  document.getElementById('shareModal').classList.add('active');
}

function closeShareModal() {
  document.getElementById('shareModal').classList.remove('active');
  currentShareSetId = null;
  currentShareSetName = null;
}

async function confirmShare() {
  if (!currentShareSetId) return;
  
  const caption = document.getElementById('shareCaption').value.trim();
  const btn = document.getElementById('btnConfirmShare');
  
  btn.disabled = true;
  btn.textContent = 'Đang chia sẻ...';
  
  try {
    const response = await fetch(`/api/sets/${currentShareSetId}/clone`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ caption: caption || null })
    });
    
    if (response.ok) {
      closeShareModal();
      window.toast.show('Đã chia sẻ bộ từ thành công!', 'success');
      updateShareCount(currentShareSetId);
      
      // Reload page to show new shared post
      setTimeout(() => window.location.reload(), 1500);
    } else {
      window.toast.show('Không thể chia sẻ bộ từ', 'error');
    }
  } catch (error) {
    window.toast.show('Lỗi: ' + error.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Chia sẻ';
  }
}

function updateShareCount(setId) {
  const card = document.querySelector(`[data-set-id="${setId}"]`);
  if (!card) return;
  
  const shareSpan = card.querySelector('.post-stats span:nth-child(3)');
  if (shareSpan) {
    // Extract current count
    const match = shareSpan.textContent.match(/(\d+) lượt chia sẻ/);
    const currentCount = match ? parseInt(match[1]) : 0;
    const newCount = currentCount + 1;
    shareSpan.textContent = `${newCount} lượt chia sẻ`;
  }
}

// Close share modal on outside click
document.addEventListener('DOMContentLoaded', function() {
  const shareModal = document.getElementById('shareModal');
  if (shareModal) {
    shareModal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeShareModal();
      }
    });
  }
});

// ========== Utility Functions ==========
function formatTime(isoString) {
  if (!isoString) return 'Vừa xong';
  
  const date = new Date(isoString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  
  if (seconds < 60) return 'Vừa xong';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} phút trước`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} giờ trước`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} ngày trước`;
  
  return date.toLocaleDateString('vi-VN');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ========== Infinite Scroll ==========
window.addEventListener('scroll', () => {
  if (isLoading || !hasMore) return;
  
  const scrollPosition = window.innerHeight + window.scrollY;
  const documentHeight = document.documentElement.scrollHeight;
  
  if (scrollPosition >= documentHeight - 500) {
    loadMorePosts();
  }
});

async function loadMorePosts() {
  isLoading = true;
  const indicator = document.getElementById('loading-indicator');
  if (indicator) indicator.style.display = 'block';
  
  try {
    const response = await fetch(`/api/feed?page=${currentPage + 1}&limit=10`);
    const data = await response.json();
    
    if (data.posts && data.posts.length > 0) {
      currentPage++;
      // appendPosts(data.posts); // TODO: Implement dynamic post rendering
    } else {
      hasMore = false;
    }
  } catch (error) {
    console.error('Error loading posts:', error);
  } finally {
    isLoading = false;
    if (indicator) indicator.style.display = 'none';
  }
}


// ========== Post/Comment Menu Functions ==========
let currentEditingPostId = null;
let currentEditingCommentId = null;
let currentEditingReplyId = null;

function togglePostMenu(event, postId) {
  event.stopPropagation();
  const menu = document.getElementById(`menu-${postId}`);
  
  // Close all other menus
  document.querySelectorAll('.menu-dropdown').forEach(m => {
    if (m.id !== `menu-${postId}`) m.classList.remove('active');
  });
  
  menu.classList.toggle('active');
}

// Close menus when clicking outside
document.addEventListener('click', (e) => {
  if (!e.target.closest('.post-menu') && !e.target.closest('.comment-menu')) {
    document.querySelectorAll('.menu-dropdown').forEach(m => {
      m.classList.remove('active');
    });
  }
});


// ========== Post Edit/Delete Functions ==========
async function deletePost(postId, event) {
  event.stopPropagation();
  
  if (!confirm('Bạn có chắc chắn muốn xóa bài viết này?')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/posts/${postId}`, {
      method: 'DELETE'
    });
    
    const data = await response.json();
    
    if (data.success) {
      window.toast.show('Đã xóa bài viết', 'success');
      // Remove post from DOM
      const postCard = document.querySelector(`[data-set-id="${postId}"]`);
      if (postCard) {
        postCard.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => postCard.remove(), 300);
      }

      // Also refresh comment count in stats
      try {
        const postCard = (commentItem && commentItem.closest('.post-card')) || null;
        const setId = postCard ? postCard.getAttribute('data-set-id') : null;
        if (setId) {
          const res = await fetch(`/api/sets/${setId}/comments`);
          const comments = await res.json();
          updateCommentCount(setId, Array.isArray(comments) ? comments.length : 0);
        }
      } catch (e) {
        console.warn('Failed to refresh comment count after delete:', e);
      }
    } else {
      window.toast.show(data.error || 'Không thể xóa bài viết', 'error');
    }
  } catch (error) {
    console.error('Error deleting post:', error);
    window.toast.show('Lỗi khi xóa bài viết', 'error');
  }
}

function editPost(postId, event) {
  event.stopPropagation();
  currentEditingPostId = postId;
  
  // Get current post content
  const postCard = document.querySelector(`[data-set-id="${postId}"]`);
  const contentElement = postCard.querySelector('.text-post-content');
  const currentContent = contentElement ? contentElement.textContent : '';
  
  // Open edit modal
  document.getElementById('editPostContent').value = currentContent;
  document.getElementById('editPostModal').classList.add('active');
  
  // Close menu
  document.getElementById(`menu-${postId}`).classList.remove('active');
}

function closeEditPostModal() {
  document.getElementById('editPostModal').classList.remove('active');
  currentEditingPostId = null;
}

async function saveEditPost() {
  if (!currentEditingPostId) return;
  
  const content = document.getElementById('editPostContent').value.trim();
  
  if (!content) {
    window.toast.show('Nội dung không được để trống', 'error');
    return;
  }
  
  try {
    const response = await fetch(`/api/posts/${currentEditingPostId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    
    const data = await response.json();
    
    if (data.success) {
      window.toast.show('Đã cập nhật bài viết', 'success');
      
      // Update post content in DOM
      const postCard = document.querySelector(`[data-set-id="${currentEditingPostId}"]`);
      const contentElement = postCard.querySelector('.text-post-content');
      if (contentElement) {
        contentElement.textContent = content;
      }
      
      // Add edited indicator
      const timeElement = postCard.querySelector('.post-time');
      if (timeElement && !timeElement.textContent.includes('Đã chỉnh sửa')) {
        const editedSpan = document.createElement('span');
        editedSpan.style.color = '#65676b';
        editedSpan.style.fontSize = '0.9em';
        editedSpan.textContent = ' · Đã chỉnh sửa';
        timeElement.appendChild(editedSpan);
      }
      
      closeEditPostModal();
    } else {
      window.toast.show(data.error || 'Không thể cập nhật bài viết', 'error');
    }
  } catch (error) {
    console.error('Error updating post:', error);
    window.toast.show('Lỗi khi cập nhật bài viết', 'error');
  }
}


// ========== Comment Edit/Delete Functions ==========
async function deleteComment(commentId, event) {
  event.stopPropagation();
  
  if (!confirm('Bạn có chắc chắn muốn xóa bình luận này?')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/comments/${commentId}`, {
      method: 'DELETE'
    });
    
    const data = await response.json();
    
    if (data.success) {
      window.toast.show('Đã xóa bình luận', 'success');
      // Remove comment from DOM
      const commentItem = document.getElementById(`comment-${commentId}`);
      if (commentItem) {
        commentItem.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => commentItem.remove(), 300);
      }
    } else {
      window.toast.show(data.error || 'Không thể xóa bình luận', 'error');
    }
  } catch (error) {
    console.error('Error deleting comment:', error);
    window.toast.show('Lỗi khi xóa bình luận', 'error');
  }
}

function editComment(commentId, event) {
  event.stopPropagation();
  currentEditingCommentId = commentId;
  
  // Get current comment content
  const commentItem = document.getElementById(`comment-${commentId}`);
  const contentElement = commentItem.querySelector('.comment-text');
  const currentContent = contentElement ? contentElement.textContent : '';
  
  // Open edit modal
  document.getElementById('editCommentContent').value = currentContent;
  document.getElementById('editCommentModal').classList.add('active');
}

function closeEditCommentModal() {
  document.getElementById('editCommentModal').classList.remove('active');
  currentEditingCommentId = null;
}

async function saveEditComment() {
  if (!currentEditingCommentId) return;
  
  const content = document.getElementById('editCommentContent').value.trim();
  
  if (!content) {
    window.toast.show('Nội dung không được để trống', 'error');
    return;
  }
  
  try {
    const response = await fetch(`/api/comments/${currentEditingCommentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    
    const data = await response.json();
    
    if (data.success) {
      window.toast.show('Đã cập nhật bình luận', 'success');
      
      // Update comment content in DOM
      const commentItem = document.getElementById(`comment-${currentEditingCommentId}`);
      const contentElement = commentItem.querySelector('.comment-text');
      if (contentElement) {
        contentElement.textContent = content;
      }
      
      // Add edited indicator
      const actionsElement = commentItem.querySelector('.comment-actions');
      if (actionsElement && !actionsElement.textContent.includes('Đã chỉnh sửa')) {
        const editedSpan = document.createElement('span');
        editedSpan.className = 'comment-time';
        editedSpan.textContent = 'Đã chỉnh sửa';
        actionsElement.appendChild(editedSpan);
      }
      
      closeEditCommentModal();
    } else {
      window.toast.show(data.error || 'Không thể cập nhật bình luận', 'error');
    }
  } catch (error) {
    console.error('Error updating comment:', error);
    window.toast.show('Lỗi khi cập nhật bình luận', 'error');
  }
}


// ========== Reply Edit/Delete Functions ==========
async function deleteReply(replyId, event) {
  event.stopPropagation();
  
  if (!confirm('Bạn có chắc chắn muốn xóa trả lời này?')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/replies/${replyId}`, {
      method: 'DELETE'
    });
    
    const data = await response.json();
    
    if (data.success) {
      window.toast.show('Đã xóa trả lời', 'success');
      // Remove reply from DOM
      const replyItem = document.getElementById(`reply-${replyId}`);
      if (replyItem) {
        replyItem.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => replyItem.remove(), 300);
      }
    } else {
      window.toast.show(data.error || 'Không thể xóa trả lời', 'error');
    }
  } catch (error) {
    console.error('Error deleting reply:', error);
    window.toast.show('Lỗi khi xóa trả lời', 'error');
  }
}

function editReply(replyId, event) {
  event.stopPropagation();
  currentEditingReplyId = replyId;
  
  // Get current reply content
  const replyItem = document.getElementById(`reply-${replyId}`);
  const contentElement = replyItem.querySelector('.comment-text');
  const currentContent = contentElement ? contentElement.textContent : '';
  
  // Open edit modal
  document.getElementById('editReplyContent').value = currentContent;
  document.getElementById('editReplyModal').classList.add('active');
}

function closeEditReplyModal() {
  document.getElementById('editReplyModal').classList.remove('active');
  currentEditingReplyId = null;
}

async function saveEditReply() {
  if (!currentEditingReplyId) return;
  
  const content = document.getElementById('editReplyContent').value.trim();
  
  if (!content) {
    window.toast.show('Nội dung không được để trống', 'error');
    return;
  }
  
  try {
    const response = await fetch(`/api/replies/${currentEditingReplyId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
    
    const data = await response.json();
    
    if (data.success) {
      window.toast.show('Đã cập nhật trả lời', 'success');
      
      // Update reply content in DOM
      const replyItem = document.getElementById(`reply-${currentEditingReplyId}`);
      const contentElement = replyItem.querySelector('.comment-text');
      if (contentElement) {
        contentElement.textContent = content;
      }
      
      // Add edited indicator
      const actionsElement = replyItem.querySelector('.comment-actions');
      if (actionsElement && !actionsElement.textContent.includes('Đã chỉnh sửa')) {
        const editedSpan = document.createElement('span');
        editedSpan.className = 'comment-time';
        editedSpan.textContent = 'Đã chỉnh sửa';
        actionsElement.appendChild(editedSpan);
      }
      
      closeEditReplyModal();
    } else {
      window.toast.show(data.error || 'Không thể cập nhật trả lời', 'error');
    }
  } catch (error) {
    console.error('Error updating reply:', error);
    window.toast.show('Lỗi khi cập nhật trả lời', 'error');
  }
}

// Add fadeOut animation
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeOut {
    from { opacity: 1; transform: scale(1); }
    to { opacity: 0; transform: scale(0.95); }
  }
`;
document.head.appendChild(style);

