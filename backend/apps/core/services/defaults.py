from apps.core.models import Tag
from apps.transactions.models import Category


DEFAULT_CATEGORIES = [
    ("Food", "utensils", "#C45C26", "expense", [
        ("Groceries", "shopping-basket", "#C45C26"),
        ("Restaurants", "utensils-crossed", "#B45309"),
        ("Delivery", "bike", "#EA580C"),
    ]),
    ("Transport", "car", "#1D4E89", "expense", [
        ("Fuel", "fuel", "#1D4E89"),
        ("Careem", "car-front", "#2563EB"),
        ("Maintenance", "wrench", "#334155"),
    ]),
    ("Bills", "receipt", "#7C3AED", "expense", []),
    ("Shopping", "shopping-bag", "#BE185D", "expense", []),
    ("Entertainment", "clapperboard", "#0F766E", "expense", []),
    ("Health", "heart-pulse", "#B91C1C", "expense", []),
    ("Education", "graduation-cap", "#4338CA", "expense", []),
    ("Travel", "plane", "#0369A1", "expense", []),
    ("Subscriptions", "repeat", "#6D28D9", "expense", []),
    ("Other", "circle", "#6B7280", "expense", []),
    ("Salary", "banknote", "#1B7A4E", "income", []),
    ("Freelance", "briefcase", "#047857", "income", []),
    ("Gift", "gift", "#0F766E", "income", []),
    ("Other income", "plus-circle", "#3F6212", "income", []),
]

DEFAULT_TAGS = ["work", "family", "travel", "thesis", "phd", "shopping", "food"]


def ensure_user_defaults(user):
    if not Category.objects.filter(user=user).exists():
        for order, (name, icon, color, kind, children) in enumerate(DEFAULT_CATEGORIES):
            parent = Category.objects.create(
                user=user,
                name=name,
                icon=icon,
                color=color,
                kind=kind,
                sort_order=order * 10,
                is_system=True,
            )
            for child_order, (cname, cicon, ccolor) in enumerate(children):
                Category.objects.create(
                    user=user,
                    name=cname,
                    parent=parent,
                    icon=cicon,
                    color=ccolor,
                    kind=kind,
                    sort_order=child_order,
                    is_system=True,
                )
    if not Tag.objects.filter(user=user).exists():
        for name in DEFAULT_TAGS:
            Tag.objects.create(user=user, name=name)
