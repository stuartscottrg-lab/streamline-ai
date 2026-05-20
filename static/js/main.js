/* ── PROGRESS BAR ── */
const progressBar = document.getElementById('progress-bar');
window.addEventListener('scroll', () => {
  const scrollTop = window.scrollY;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  progressBar.style.width = (scrollTop / docHeight * 100) + '%';
});

/* ── NAVBAR SCROLL ── */
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 40);
});

/* ── HAMBURGER MENU ── */
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobile-menu');
hamburger.addEventListener('click', () => {
  const open = mobileMenu.classList.toggle('open');
  hamburger.setAttribute('aria-expanded', open);
});
document.querySelectorAll('.mob-link, .mob-cta').forEach(link => {
  link.addEventListener('click', () => mobileMenu.classList.remove('open'));
});

/* ── FAQ ACCORDION ── */
document.querySelectorAll('.faq-q').forEach(btn => {
  btn.addEventListener('click', () => {
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    document.querySelectorAll('.faq-q').forEach(b => {
      b.setAttribute('aria-expanded', 'false');
      b.nextElementSibling.classList.remove('open');
    });
    if (!expanded) {
      btn.setAttribute('aria-expanded', 'true');
      btn.nextElementSibling.classList.add('open');
    }
  });
});

/* ── LEAD FORM ── */
const leadForm = document.getElementById('lead-form');
if (leadForm) {
  leadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('form-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoading = document.getElementById('btn-loading');
    const successEl = document.getElementById('form-success');
    const errorEl = document.getElementById('form-error');

    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    successEl.style.display = 'none';
    errorEl.style.display = 'none';

    const data = {
      name: document.getElementById('name').value,
      email: document.getElementById('email').value,
      firm_type: document.getElementById('firm-type').value,
    };

    try {
      const res = await fetch('/api/lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        successEl.style.display = 'flex';
        leadForm.reset();
      } else {
        errorEl.style.display = 'block';
      }
    } catch {
      errorEl.style.display = 'block';
    } finally {
      btn.disabled = false;
      btnText.style.display = 'inline';
      btnLoading.style.display = 'none';
    }
  });
}

/* ── CHAT WIDGET ── */
const chatToggle = document.getElementById('chat-toggle');
const chatBox = document.getElementById('chat-box');
const chatClose = document.getElementById('chat-close');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');
const chatMessages = document.getElementById('chat-messages');
const chatNotif = document.getElementById('chat-notif');
const chatIconOpen = document.getElementById('chat-icon-open');
const chatIconClose = document.getElementById('chat-icon-close');
const quickReplies = document.getElementById('quick-replies');

let chatOpen = false;
let conversationHistory = [];

function toggleChat() {
  chatOpen = !chatOpen;
  chatBox.classList.toggle('chat-hidden', !chatOpen);
  chatBox.classList.toggle('chat-visible', chatOpen);
  chatIconOpen.style.display = chatOpen ? 'none' : 'block';
  chatIconClose.style.display = chatOpen ? 'block' : 'none';
  if (chatOpen) {
    chatNotif.style.display = 'none';
    chatInput.focus();
  }
}

chatToggle.addEventListener('click', toggleChat);
chatClose.addEventListener('click', toggleChat);

function appendMessage(text, role) {
  const div = document.createElement('div');
  div.className = `msg msg-${role}`;
  div.innerHTML = `<div class="chat-bubble">${escapeHtml(text)}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTyping() {
  const div = document.createElement('div');
  div.className = 'msg msg-ai';
  div.id = 'typing-indicator';
  div.innerHTML = '<div class="chat-bubble typing"><span></span><span></span><span></span></div>';
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function sendMessage(text) {
  if (!text.trim()) return;
  appendMessage(text, 'user');
  chatInput.value = '';
  quickReplies.style.display = 'none';

  conversationHistory.push({ role: 'user', content: text });

  const typing = appendTyping();
  chatSend.disabled = true;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: conversationHistory }),
    });
    const data = await res.json();
    removeTyping();
    const reply = data.reply || "Thanks for your message! Our team will be in touch shortly.";
    appendMessage(reply, 'ai');
    conversationHistory.push({ role: 'assistant', content: reply });
  } catch {
    removeTyping();
    appendMessage("Sorry, I'm having a moment. Please email us at hello@streamlineai.co.uk", 'ai');
  } finally {
    chatSend.disabled = false;
  }
}

chatSend.addEventListener('click', () => sendMessage(chatInput.value));
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(chatInput.value); }
});

document.querySelectorAll('.qr-btn').forEach(btn => {
  btn.addEventListener('click', () => sendMessage(btn.dataset.msg));
});

/* ── INTERSECTION OBSERVER — fade in on scroll ── */
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.service-card, .case-card, .testi-card, .step-card, .problem-card, .as-card').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(24px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});
