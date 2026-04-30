from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from pathlib import Path
import json

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PRODUCTS_FILE = DATA_DIR / "products.json"
ORDERS_FILE = DATA_DIR / "orders.json"

DEFAULT_PRODUCTS = [
    {
        "id": 1,
        "name": "Aero Runner X1",
        "price": 180,
        "stock": 12,
        "category": "Running",
        "image": "images/shoe1.svg",
        "accent": "cyan"
    },
    {
        "id": 2,
        "name": "Street High V2",
        "price": 190,
        "stock": 8,
        "category": "Sneakers",
        "image": "images/shoe2.svg",
        "accent": "red"
    },
    {
        "id": 3,
        "name": "Sunburst Low",
        "price": 150,
        "stock": 15,
        "category": "Casual",
        "image": "images/shoe3.svg",
        "accent": "orange"
    },
    {
        "id": 4,
        "name": "Glide Max 90",
        "price": 170,
        "stock": 10,
        "category": "Sport",
        "image": "images/shoe4.svg",
        "accent": "blue"
    },
    {
        "id": 5,
        "name": "Velocity Air Pro",
        "price": 160,
        "stock": 6,
        "category": "Featured",
        "image": "images/hero-shoe.svg",
        "accent": "cyan"
    },
]

FEATURED_INFO = {
    "description": "Lightweight comfort, bold street style, and everyday performance in one premium silhouette."
}



def save_orders(orders):
    DATA_DIR.mkdir(exist_ok=True)
    ORDERS_FILE.write_text(json.dumps(orders, indent=4), encoding="utf-8")


def load_orders():
    if not ORDERS_FILE.exists():
        save_orders([])
        return []

    try:
        orders = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        if isinstance(orders, list):
            return orders
    except json.JSONDecodeError:
        pass

    save_orders([])
    return []


def save_products(products):
    DATA_DIR.mkdir(exist_ok=True)
    PRODUCTS_FILE.write_text(json.dumps(products, indent=4), encoding="utf-8")


def load_products():
    if not PRODUCTS_FILE.exists():
        save_products(DEFAULT_PRODUCTS)
        return DEFAULT_PRODUCTS.copy()

    try:
        products = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        save_products(DEFAULT_PRODUCTS)
        return DEFAULT_PRODUCTS.copy()

    # Make sure older product files still get a stock value.
    changed = False
    for default_product in DEFAULT_PRODUCTS:
        product = next((p for p in products if p.get("id") == default_product["id"]), None)
        if product is None:
            products.append(default_product.copy())
            changed = True
        elif "stock" not in product:
            product["stock"] = default_product["stock"]
            changed = True

    if changed:
        save_products(products)

    return products


@app.route('/')
def index():
    products = load_products()
    featured = next((p for p in products if p["id"] == 5), products[0]).copy()
    featured["description"] = FEATURED_INFO["description"]
    return render_template('index.html', products=products, featured=featured, year=datetime.now().year)


@app.get('/admin')
def admin():
    products = load_products()
    status = request.args.get('status')
    message = request.args.get('message')
    return render_template('admin.html', products=products, year=datetime.now().year, status=status, message=message)


@app.post('/admin/update-product')
def update_product():
    products = load_products()

    try:
        product_id = int(request.form.get('product_id', 0))
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
    except (TypeError, ValueError):
        return redirect(url_for('admin', status='error', message='Please enter a valid price and stock.'))

    if price < 0 or stock < 0:
        return redirect(url_for('admin', status='error', message='Price and stock cannot be negative.'))

    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return redirect(url_for('admin', status='error', message='Product not found.'))

    product['price'] = round(price, 2)
    product['stock'] = stock
    save_products(products)

    return redirect(url_for('admin', status='success', message=f"{product['name']} updated successfully."))


@app.post('/order')
def order():
    data = request.get_json(force=True)

    try:
        product_id = int(data.get('product_id', 0))
        quantity = int(data.get('quantity', 1))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid order details.'}), 400

    customer_name = (data.get('customer_name') or '').strip()
    if not customer_name:
        return jsonify({'success': False, 'message': 'Please enter customer name first.'}), 400

    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)

    if not product:
        return jsonify({'success': False, 'message': 'Product not found.'}), 404
    if quantity < 1:
        return jsonify({'success': False, 'message': 'Quantity must be at least 1.'}), 400
    if product['stock'] <= 0:
        return jsonify({'success': False, 'message': f"{product['name']} is out of stock."}), 400
    if quantity > product['stock']:
        return jsonify({'success': False, 'message': f"Only {product['stock']} item(s) left for {product['name']}."}), 400

    product['stock'] -= quantity
    save_products(products)

    total = product['price'] * quantity
    order_info = {
        'order_id': datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'customer_name': customer_name,
        'product': product['name'],
        'quantity': quantity,
        'price': product['price'],
        'total': total,
        'remaining_stock': product['stock'],
        'created_at': datetime.now().strftime('%b %d, %Y %I:%M %p')
    }

    orders = load_orders()
    orders.insert(0, order_info)
    save_orders(orders)

    return jsonify({
        'success': True,
        'message': f"Order placed for {product['name']}! Stock left: {product['stock']}",
        'order': order_info,
        'order_count': len(orders),
        'product_id': product['id'],
        'new_stock': product['stock']
    })


@app.get('/orders')
def orders():
    return jsonify(load_orders()[:8])


if __name__ == '__main__':
    app.run(debug=True)
