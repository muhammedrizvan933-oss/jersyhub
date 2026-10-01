// JerseyHub - Main JavaScript

document.addEventListener('DOMContentLoaded', () => {
  initSearchAutocomplete();
  initSizePicker();
  initAjaxAddToCart();
  initCartCounters();
  initProductShare();
});

// 1. Live Search Autocomplete
function initSearchAutocomplete() {
  const searchInput = document.getElementById('navbar-search-input');
  const dropdown = document.getElementById('navbar-search-dropdown');
  if (!searchInput || !dropdown) return;

  let debounceTimer;

  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    const query = e.target.value.trim();

    if (query.length < 2) {
      dropdown.style.display = 'none';
      dropdown.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search/autocomplete?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(items => {
          if (!items || items.length === 0) {
            dropdown.innerHTML = `<div class="p-3 text-muted text-center small">No jerseys found for "${query}"</div>`;
            dropdown.style.display = 'block';
            return;
          }

          dropdown.innerHTML = items.map(p => `
            <a href="/products/${p.slug}" class="search-result-item">
              <img src="${p.image}" class="search-result-thumb" alt="${p.name}">
              <div class="flex-grow-1">
                <div class="fw-bold small text-truncate" style="max-width: 200px;">${p.name}</div>
                <div class="text-muted" style="font-size: 0.75rem;">${p.team}</div>
              </div>
              <div class="fw-bold text-accent" style="color: #00e676;">₹${p.price.toFixed(2)}</div>
            </a>
          `).join('');
          dropdown.style.display = 'block';
        })
        .catch(err => console.error(err));
    }, 250);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });
}

// 2. Size Picker in Product Detail
function initSizePicker() {
  const sizeButtons = document.querySelectorAll('.size-picker-btn');
  const variantInput = document.getElementById('selected-variant-id');
  const stockNotice = document.getElementById('selected-stock-notice');
  const addToCartBtn = document.getElementById('btn-add-to-cart');

  sizeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.classList.contains('disabled')) return;

      sizeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const variantId = btn.dataset.variantId;
      const stock = parseInt(btn.dataset.stock, 10);

      if (variantInput) variantInput.value = variantId;

      if (stockNotice) {
        if (stock <= 5) {
          stockNotice.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-fire"></i> Hurry! Only ${stock} left in stock!</span>`;
        } else {
          stockNotice.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill"></i> In Stock (${stock} available)</span>`;
        }
      }

      if (addToCartBtn) {
        addToCartBtn.removeAttribute('disabled');
        addToCartBtn.innerHTML = '<i class="bi bi-bag-plus"></i> Add to Cart';
      }
    });
  });
}

// 3. AJAX Add to Cart
function initAjaxAddToCart() {
  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (!form.classList.contains('ajax-add-cart-form')) return;

    e.preventDefault();
    const formData = new FormData(form);

    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'success');
        updateCartBadge(data.cart_count);
      } else {
        showToast(data.message, 'danger');
      }
    })
    .catch(() => {
      form.submit(); // fallback to normal submit
    });
  });
}

// 4. Cart counters & Toast
function updateCartBadge(count) {
  const badges = document.querySelectorAll('.cart-counter-badge');
  badges.forEach(b => {
    b.textContent = count;
    b.classList.remove('d-none');
  });
}

function showToast(message, type = 'success') {
  let toastContainer = document.getElementById('jh-toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'jh-toast-container';
    toastContainer.style.cssText = 'position: fixed; bottom: 24px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bgClass = type === 'success' ? '#00e676' : (type === 'danger' ? '#ef4444' : '#3b82f6');
  const textClass = type === 'success' ? '#0b0f19' : '#ffffff';

  toast.style.cssText = `background: ${bgClass}; color: ${textClass}; font-weight: 700; font-size: 0.9rem; padding: 12px 20px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 10px; transition: all 0.3s; opacity: 0; transform: translateY(10px);`;
  toast.innerHTML = `<i class="bi bi-${type === 'success' ? 'check-circle-fill' : 'exclamation-triangle-fill'}"></i> ${message}`;

  toastContainer.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function initCartCounters() {
  // Sync live cart count on initial load
  fetch('/api/cart/count')
    .then(res => res.json())
    .then(d => {
      if (d.count !== undefined) updateCartBadge(d.count);
    })
    .catch(() => {});
}

// 5. Product sharing
function initProductShare() {
  const shareButton = document.getElementById('share-product-btn');
  const status = document.getElementById('share-product-status');
  if (!shareButton) return;

  shareButton.addEventListener('click', async () => {
    const shareData = {
      title: shareButton.dataset.shareTitle || document.title,
      text: `Check out ${shareButton.dataset.shareTitle || 'this jersey'} on JerseyHub`,
      url: window.location.href
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
        setShareStatus('Product shared successfully.');
        return;
      }

      await copyShareUrl(shareData.url);
      setShareStatus('Product link copied to your clipboard.');
    } catch (error) {
      if (error.name === 'AbortError') return;
      setShareStatus('Unable to share this product right now.');
    }
  });

  function setShareStatus(message) {
    if (status) status.textContent = message;
    showToast(message, message.includes('Unable') ? 'danger' : 'success');
  }
}

async function copyShareUrl(url) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(url);
    return;
  }

  const input = document.createElement('textarea');
  input.value = url;
  input.setAttribute('readonly', '');
  input.style.position = 'fixed';
  input.style.opacity = '0';
  document.body.appendChild(input);
  input.select();
  const copied = document.execCommand('copy');
  input.remove();

  if (!copied) {
    throw new Error('Clipboard access was not available.');
  }
}
