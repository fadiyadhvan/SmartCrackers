def recommend_products(products, budget, people, occasion):

    recommendations = []

    for product in products:

        price = float(product["price"])
        category = product["category"].lower()

        # Product must be within budget
        if price > budget:
            continue

        score = 0

        # Budget match
        if price <= budget:
            score += 2

        # More people → family products
        if people >= 4 and "family" in category:
            score += 3

        # Diwali → sparklers and gift products
        if occasion == "Diwali":
            if "sparkler" in category:
                score += 3

            if "gift" in category:
                score += 2

        # Festival → gift products
        if occasion == "Festival":
            if "gift" in category:
                score += 3

        # Family celebration
        if occasion == "Family Celebration":
            if "family" in category:
                score += 3

        recommendations.append(
            (score, product)
        )

    # Highest score first
    recommendations.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        product
        for score, product in recommendations
    ]