from flask import Flask, render_template, request, redirect, session
import pymysql
import uuid

# AI CHATBOT
from chatbot import chatbot_response


app = Flask(__name__)
app.secret_key = "smartcrackers_secret_key"


# =========================
# DATABASE CONNECTION
# =========================
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="smartuser",
        password="smart123",
        database="smartcrackers",
        cursorclass=pymysql.cursors.DictCursor
    )


# =========================
# HOME PAGE
# =========================
@app.route("/")
def home():
    return render_template("index.html")


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        if not name or not email or not phone or not password:
            return "Please fill all fields"

        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users
                (name, email, phone, password)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, phone, password)
            )

            connection.commit()

        except pymysql.err.IntegrityError:
            connection.close()
            return "Email already registered"

        connection.close()

        return redirect("/login")

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email=%s AND password=%s
            """,
            (email, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect("/")

        return "Invalid email or password"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# PRODUCTS
# =========================
@app.route("/products")
def products():

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    max_price = request.args.get("max_price", "")

    connection = get_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    values = []

    if search:
        query += " AND name LIKE %s"
        values.append("%" + search + "%")

    if category:
        query += " AND category=%s"
        values.append(category)

    if max_price:
        query += " AND price <= %s"
        values.append(max_price)

    query += " ORDER BY id DESC"

    cursor.execute(query, values)

    products_list = cursor.fetchall()

    connection.close()

    return render_template(
        "products.html",
        products=products_list
    )


# =========================
# ADD TO CART
# =========================
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    product_id = request.form.get("product_id")

    if not product_id:
        return redirect("/products")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id=%s",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        connection.close()
        return "Product not found"

    if product["stock"] <= 0:
        connection.close()
        return "Product is out of stock"

    cursor.execute(
        "SELECT * FROM cart WHERE product_id=%s",
        (product_id,)
    )

    existing = cursor.fetchone()

    if existing:

        new_quantity = existing["quantity"] + 1

        if new_quantity > product["stock"]:
            connection.close()
            return "Maximum available stock reached"

        cursor.execute(
            """
            UPDATE cart
            SET quantity=%s
            WHERE id=%s
            """,
            (new_quantity, existing["id"])
        )

    else:

        cursor.execute(
            """
            INSERT INTO cart
            (product_id, quantity)
            VALUES (%s, %s)
            """,
            (product_id, 1)
        )

    connection.commit()
    connection.close()

    return redirect("/cart")


# =========================
# CART
# =========================
@app.route("/cart")
def cart():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            cart.id,
            cart.product_id,
            cart.quantity,
            products.name,
            products.price,
            products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        ORDER BY cart.id DESC
        """
    )

    cart_items = cursor.fetchall()

    total = 0

    for item in cart_items:

        item_total = float(item["price"]) * item["quantity"]

        item["item_total"] = item_total

        total += item_total

    connection.close()

    return render_template(
        "cart.html",
        cart=cart_items,
        total=total
    )


# =========================
# UPDATE CART QUANTITY
# =========================
@app.route("/update_cart/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):

    quantity = request.form.get("quantity")

    try:
        quantity = int(quantity)
    except:
        quantity = 1

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT cart.*, products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        WHERE cart.id=%s
        """,
        (cart_id,)
    )

    item = cursor.fetchone()

    if not item:
        connection.close()
        return redirect("/cart")

    if quantity < 1:
        quantity = 1

    if quantity > item["stock"]:
        quantity = item["stock"]

    cursor.execute(
        """
        UPDATE cart
        SET quantity=%s
        WHERE id=%s
        """,
        (quantity, cart_id)
    )

    connection.commit()
    connection.close()

    return redirect("/cart")


# =========================
# REMOVE FROM CART
# =========================
@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM cart WHERE id=%s",
        (cart_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/cart")


# =========================
# CLEAR CART
# =========================
@app.route("/clear_cart")
def clear_cart():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM cart")

    connection.commit()
    connection.close()

    return redirect("/cart")


# =========================
# CHECKOUT
# =========================
@app.route("/checkout")
def checkout():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            cart.id,
            cart.product_id,
            cart.quantity,
            products.name,
            products.price,
            products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        """
    )

    cart_items = cursor.fetchall()

    total = 0

    for item in cart_items:
        total += float(item["price"]) * item["quantity"]

    connection.close()

    if not cart_items:
        return redirect("/cart")

    return render_template(
        "checkout.html",
        cart=cart_items,
        total=total
    )


# =========================
# PLACE ORDER
# =========================
@app.route("/place_order", methods=["POST"])
def place_order():

    customer_name = request.form.get("customer_name")
    phone = request.form.get("phone")
    address = request.form.get("address")
    city = request.form.get("city")
    payment = request.form.get("payment")

    if not customer_name or not phone or not address or not city or not payment:
        return "Please fill all checkout fields"

    connection = get_connection()
    cursor = connection.cursor()

    # Get cart
    cursor.execute(
        """
        SELECT
            cart.id,
            cart.product_id,
            cart.quantity,
            products.name,
            products.price,
            products.stock
        FROM cart
        JOIN products
        ON cart.product_id = products.id
        """
    )

    cart_items = cursor.fetchall()

    if not cart_items:
        connection.close()
        return redirect("/cart")

    total = 0

    # Check stock
    for item in cart_items:

        if item["quantity"] > item["stock"]:
            connection.close()

            return (
                "Not enough stock for "
                + item["name"]
            )

        total += float(item["price"]) * item["quantity"]

    # Create order ID
    order_id = "SC" + uuid.uuid4().hex[:10].upper()

    # Insert order
    cursor.execute(
        """
        INSERT INTO orders
        (
            order_id,
            customer_name,
            phone,
            address,
            city,
            payment,
            total,
            status,
            mobile
        )
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            order_id,
            customer_name,
            phone,
            address,
            city,
            payment,
            total,
            "Confirmed",
            phone
        )
    )

    # Reduce stock
    for item in cart_items:

        new_stock = item["stock"] - item["quantity"]

        cursor.execute(
            """
            UPDATE products
            SET stock=%s
            WHERE id=%s
            """,
            (
                new_stock,
                item["product_id"]
            )
        )

    # Clear cart
    cursor.execute("DELETE FROM cart")

    connection.commit()
    connection.close()

    return render_template(
        "thankyou.html",
        order_id=order_id,
        customer_name=customer_name,
        total=total
    )


# =========================
# ORDERS
# =========================
@app.route("/orders")
def orders():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM orders
        ORDER BY id DESC
        """
    )

    orders_list = cursor.fetchall()

    connection.close()

    return render_template(
        "orders.html",
        orders=orders_list
    )


# =========================
# AI RECOMMENDATION
# =========================
@app.route("/recommendation")
def recommendation():

    return render_template(
        "recommendation.html"
    )


# =========================
# AI CHATBOT
# =========================
@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():

    message = ""
    response = ""

    if request.method == "POST":

        message = request.form.get(
            "message",
            ""
        ).strip()

        if message:

            response = chatbot_response(
                message
            )

    return render_template(
        "chatbot.html",
        message=message,
        response=response
    )


# =========================
# RUN APPLICATION
# =========================
if __name__ == "__main__":

    app.run(
        debug=True
    )