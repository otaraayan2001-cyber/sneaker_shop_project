let cartCount = 0;
let selectedProduct = null;

const cartDrawer = document.getElementById('cartDrawer');
const drawerBackdrop = document.getElementById('drawerBackdrop');
const cartCountEl = document.getElementById('cartCount');
const orderListEl = document.getElementById('orderList');
const searchInput = document.getElementById('searchInput');
const productCards = Array.from(document.querySelectorAll('.product-card'));

const orderModal = document.getElementById('orderModal');
const orderModalBackdrop = document.getElementById('orderModalBackdrop');
const orderForm = document.getElementById('orderForm');
const modalProductId = document.getElementById('modalProductId');
const modalProductName = document.getElementById('modalProductName');
const modalProductPrice = document.getElementById('modalProductPrice');
const modalProductStock = document.getElementById('modalProductStock');
const customerName = document.getElementById('customerName');
const orderQuantity = document.getElementById('orderQuantity');

function toggleCart(forceState) {
  const shouldOpen = typeof forceState === 'boolean' ? forceState : !cartDrawer.classList.contains('open');
  cartDrawer.classList.toggle('open', shouldOpen);
  drawerBackdrop.classList.toggle('show', shouldOpen);
}

document.getElementById('cartButton').addEventListener('click', async () => {
  await loadOrders();

  if (cartCount <= 0) {
    showToast('Place an order first before viewing history.');
    return;
  }

  toggleCart();
});

function openOrderModal(productId) {
  const product = PRODUCTS.find(item => item.id === productId);
  if (!product) {
    showToast('Product not found.');
    return;
  }

  if (product.stock <= 0) {
    showToast(`${product.name} is out of stock.`);
    return;
  }

  selectedProduct = product;
  modalProductId.value = product.id;
  modalProductName.textContent = product.name;
  modalProductPrice.textContent = `$${Number(product.price).toFixed(2)}`;
  modalProductStock.textContent = `Available Stock: ${product.stock}`;
  orderQuantity.max = product.stock;
  orderQuantity.value = 1;
  customerName.value = '';

  orderModal.classList.add('show');
  orderModalBackdrop.classList.add('show');
  orderModal.setAttribute('aria-hidden', 'false');
  setTimeout(() => customerName.focus(), 120);
}

function closeOrderModal() {
  orderModal.classList.remove('show');
  orderModalBackdrop.classList.remove('show');
  orderModal.setAttribute('aria-hidden', 'true');
  selectedProduct = null;
}

orderForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  if (!selectedProduct) {
    showToast('Please select a product first.');
    return;
  }

  const quantity = Number(orderQuantity.value);
  if (quantity < 1) {
    showToast('Quantity must be at least 1.');
    return;
  }

  if (quantity > selectedProduct.stock) {
    showToast(`Only ${selectedProduct.stock} item(s) left.`);
    return;
  }

  await placeOrder(selectedProduct.id, customerName.value.trim(), quantity);
});

async function placeOrder(productId, name, quantity) {
  try {
    const response = await fetch('/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, customer_name: name, quantity })
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      showToast(data.message || 'Failed to place order.');
      return;
    }

    cartCount = data.order_count || cartCount + 1;
    cartCountEl.textContent = cartCount;
    updateProductStock(data.product_id, data.new_stock);

    const product = PRODUCTS.find(item => item.id === data.product_id);
    if (product) {
      product.stock = data.new_stock;
    }

    closeOrderModal();
    showToast(data.message);
    await loadOrders();
    toggleCart(true);
  } catch (error) {
    showToast('Something went wrong.');
  }
}

async function loadOrders() {
  try {
    const response = await fetch('/orders');
    const orders = await response.json();
    cartCount = orders.length;
    cartCountEl.textContent = cartCount;

    if (!orders.length) {
      orderListEl.innerHTML = '<div class="empty-state">No orders yet. Place an order first.</div>';
      return;
    }

    orderListEl.innerHTML = orders.map(order => `
      <div class="order-item">
        <h4>${order.product}</h4>
        <div class="order-customer">Customer: ${order.customer_name || 'Walk-in Customer'}</div>
        <div class="order-meta"><span>Qty: ${order.quantity}</span><span>Total: $${Number(order.total).toFixed(2)}</span></div>
        <div class="order-meta"><span>${order.created_at}</span></div>
      </div>
    `).join('');
  } catch (error) {
    orderListEl.innerHTML = '<div class="empty-state">Unable to load orders.</div>';
  }
}

function updateProductStock(productId, newStock) {
  const stockEl = document.getElementById(`stock-${productId}`);
  if (stockEl) {
    stockEl.textContent = `Stock: ${newStock}`;
    stockEl.classList.toggle('out', newStock <= 0);
  }

  const buttons = document.querySelectorAll(`button[onclick="openOrderModal(${productId})"]`);
  buttons.forEach(button => {
    button.disabled = newStock <= 0;
  });
}

function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 250);
  }, 2200);
}

searchInput.addEventListener('input', (e) => {
  const value = e.target.value.trim().toLowerCase();
  productCards.forEach(card => {
    const haystack = card.dataset.name;
    card.style.display = haystack.includes(value) ? '' : 'none';
  });
});

loadOrders();
