def chatbot_response(message):

    message = message.lower().strip()

    # Greeting
    if "hello" in message or "hi" in message or "hey" in message:
        return "Hello! 👋 Welcome to SmartCrackers. How can I help you today?"

    # Diwali
    elif "diwali" in message:
        return "🎆 For Diwali, I recommend Sparklers, Flower Pots and Family Celebration Packs."

    # Family
    elif "family" in message:
        return "👨‍👩‍👧‍👦 For a family celebration, I recommend the Family Celebration Pack."

    # Budget
    elif "budget" in message:
        return "💰 Tell me your budget, for example: 'Suggest products under ₹500'."

    # Cheap products
    elif "cheap" in message or "low price" in message:
        return "💰 Our Sparkler Pack costs ₹150 and Flower Pot Pack costs ₹350."

    # Products
    elif "product" in message or "products" in message:
        return "🎆 We have Sparklers, Flower Pots, Gift Boxes and Family Celebration Packs."

    # Cart
    elif "cart" in message:
        return "🛒 You can add products to your cart and then open the Cart page to checkout."

    # Order
    elif "order" in message:
        return "📦 You can place your order from the Cart → Checkout page."

    # Price
    elif "price" in message or "cost" in message:
        return "💰 Our demo products start from ₹150."

    # Thank you
    elif "thank" in message:
        return "😊 You're welcome! Happy shopping with SmartCrackers! 🎆"

    # Default
    else:
        return (
            "🤖 I can help you with Products, Prices, "
            "Diwali, Family celebrations, Budget, Cart and Orders."
        )