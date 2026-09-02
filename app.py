from flask import Flask, render_template, request, redirect, session
import pymysql
import uuid

app = Flask(__name__)

# ============================================================
# SECRET KEY
# ============================================================

app.secret_key = "smartcrackers_secret_key_123"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="smartuser",
        password="smart123",
        database="smartcrackers",
        cursorclass=pymysql.cursors.DictCursor
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()
            connection.close()

            return "Email already registered. Please login."

        cursor.execute(
            """
            INSERT INTO users
            (name, email, phone, password)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, phone, password)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/login")

    return render_template("register.html")


# ============================================================
# LOGIN
# ============================================================

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

        cursor.close()
        connection.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect("/products")

        return "Invalid email or password."

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# PRODUCTS
# ============================================================

@app.route("/products")
def products():

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    price = request.args.get("price", "")

    connection = get_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM products WHERE 1=1"
    values = []

    # SEARCH
    if search:

        query += " AND name LIKE %s"
        values.append("%" + search + "%")

    # CATEGORY
    if category:

        query += " AND category=%s"
        values.append(category)

    # PRICE
    if price:

        query += " AND price <= %s"
        values.append(price)

    query += " ORDER BY id"

    cursor.execute(query, values)

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "products.html",
        products=products,
        search=search,
        category=category,
        price=price
    )


# ============================================================
# ADD TO CART
# ============================================================

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    product_id = request.form.get("product_id")

    if not product_id:

        return "Product ID is missing."

    connection = get_connection()
    cursor = connection.cursor()

    # CHECK PRODUCT
    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE id=%s
        """,
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:

        cursor.close()
        connection.close()

        return "Product not found."

    # CHECK STOCK
    if product["stock"] <= 0:

        cursor.close()
        connection.close()

        return "Sorry, this product is out of stock."

    # CHECK CART
    cursor.execute(
        """
        SELECT *
        FROM cart
        WHERE product_id=%s
        """,
        (product_id,)
    )

    cart_item = cursor.fetchone()

    if cart_item:

        if cart_item["quantity"] >= product["stock"]:

            cursor.close()
            connection.close()

            return "You cannot add more than available stock."

        cursor.execute(
            """
            UPDATE cart
            SET quantity = quantity + 1
            WHERE product_id=%s
            """,
            (product_id,)
        )

    else:

        cursor.execute(
            """
            INSERT INTO cart
            (product_id, quantity)
            VALUES (%s, 1)
            """,
            (product_id,)
        )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/cart")


# ============================================================
# CART
# ============================================================

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
            cart.created_at,
            products.name,
            products.price,
            products.description,
            products.stock

        FROM cart

        INNER JOIN products
        ON cart.product_id = products.id

        ORDER BY cart.id DESC
        """
    )

    cart_items = cursor.fetchall()

    cursor.close()
    connection.close()

    total = 0

    for item in cart_items:

        total += float(item["price"]) * item["quantity"]

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


# ============================================================
# UPDATE CART
# ============================================================

@app.route("/update_cart/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):

    quantity = request.form.get("quantity")

    try:

        quantity = int(quantity)

    except:

        return "Invalid quantity."

    if quantity < 1:

        return redirect("/cart")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            cart.product_id,
            products.stock

        FROM cart

        INNER JOIN products
        ON cart.product_id = products.id

        WHERE cart.id=%s
        """,
        (cart_id,)
    )

    item = cursor.fetchone()

    if not item:

        cursor.close()
        connection.close()

        return "Cart item not found."

    if quantity > item["stock"]:

        cursor.close()
        connection.close()

        return "Quantity is greater than available stock."

    cursor.execute(
        """
        UPDATE cart
        SET quantity=%s
        WHERE id=%s
        """,
        (quantity, cart_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/cart")


# ============================================================
# REMOVE FROM CART
# ============================================================

@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM cart
        WHERE id=%s
        """,
        (cart_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/cart")


# ============================================================
# CLEAR CART
# ============================================================

@app.route("/clear_cart")
def clear_cart():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM cart")

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/cart")


# ============================================================
# CHECKOUT
# ============================================================

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
            products.price

        FROM cart

        INNER JOIN products
        ON cart.product_id = products.id
        """
    )

    cart_items = cursor.fetchall()

    cursor.close()
    connection.close()

    if not cart_items:

        return redirect("/cart")

    total = 0

    for item in cart_items:

        total += float(item["price"]) * item["quantity"]

    customer_name = session.get("user_name", "")

    customer_email = session.get("user_email", "")

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=total,
        customer_name=customer_name,
        customer_email=customer_email
    )


# ============================================================
# PLACE ORDER
# ============================================================

@app.route("/place_order", methods=["POST"])
def place_order():

    customer_name = request.form.get("customer_name")
    phone = request.form.get("phone")
    address = request.form.get("address")
    city = request.form.get("city")
    payment = request.form.get("payment")

    # VALIDATION

    if not customer_name:

        return "Please enter customer name."

    if not phone:

        return "Please enter phone number."

    if not address:

        return "Please enter address."

    if not city:

        return "Please enter city."

    if not payment:

        return "Please select payment method."

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ====================================================
        # GET CART
        # ====================================================

        cursor.execute(
            """
            SELECT
                cart.product_id,
                cart.quantity,
                products.name,
                products.price,
                products.stock

            FROM cart

            INNER JOIN products
            ON cart.product_id = products.id
            """
        )

        cart_items = cursor.fetchall()

        if not cart_items:

            cursor.close()
            connection.close()

            return "Your cart is empty."


        # ====================================================
        # CHECK STOCK + CALCULATE TOTAL
        # ====================================================

        total = 0

        for item in cart_items:

            if item["quantity"] > item["stock"]:

                cursor.close()
                connection.close()

                return (
                    "Not enough stock for "
                    + item["name"]
                )

            total += (
                float(item["price"])
                * item["quantity"]
            )


        # ====================================================
        # CREATE ORDER ID
        # ====================================================

        order_id = (
            "SC"
            + uuid.uuid4().hex[:8].upper()
        )


        # ====================================================
        # INSERT ORDER
        # ====================================================

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
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
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


        # ====================================================
        # REDUCE PRODUCT STOCK
        # ====================================================

        for item in cart_items:

            cursor.execute(
                """
                UPDATE products

                SET stock = stock - %s

                WHERE id=%s
                """,
                (
                    item["quantity"],
                    item["product_id"]
                )
            )


        # ====================================================
        # EMPTY CART
        # ====================================================

        cursor.execute(
            "DELETE FROM cart"
        )


        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()

        cursor.close()
        connection.close()


        # ====================================================
        # THANK YOU PAGE
        # ====================================================

        return render_template(
            "thankyou.html",
            order_id=order_id,
            total=total
        )


    except Exception as e:

        connection.rollback()

        cursor.close()
        connection.close()

        return "Order error: " + str(e)


# ============================================================
# ORDERS
# ============================================================

@app.route("/orders")
def orders():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM orders
        ORDER BY order_date DESC
        """
    )

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "orders.html",
        orders=orders
    )


# ============================================================
# AI RECOMMENDATION
# ============================================================

@app.route("/recommendation")
def recommendation():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM products
        WHERE stock > 0
        ORDER BY price ASC
        """
    )

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "recommendation.html",
        products=products
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )