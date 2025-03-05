# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import uuid
from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil


class ProductEntity(Entity):
    """Generate product data.

    This class generates realistic product data including product IDs,
    names, descriptions, prices, categories, and other product attributes.
    """

    # Product categories
    PRODUCT_CATEGORIES = [
        "ELECTRONICS",
        "CLOTHING",
        "HOME_GOODS",
        "BEAUTY",
        "HEALTH",
        "SPORTS",
        "TOYS",
        "BOOKS",
        "FOOD",
        "BEVERAGES",
        "AUTOMOTIVE",
        "OFFICE_SUPPLIES",
        "PET_SUPPLIES",
        "JEWELRY",
        "FURNITURE",
    ]

    # Product conditions
    PRODUCT_CONDITIONS = ["NEW", "USED", "REFURBISHED", "OPEN_BOX", "DAMAGED"]

    # Product availability
    PRODUCT_AVAILABILITY = ["IN_STOCK", "OUT_OF_STOCK", "BACK_ORDERED", "DISCONTINUED", "PRE_ORDER"]

    # Product brands (sample)
    PRODUCT_BRANDS = [
        "ACME",
        "TechPro",
        "HomeStyle",
        "FashionForward",
        "GourmetDelight",
        "SportsMaster",
        "KidsFun",
        "BeautyEssentials",
        "HealthFirst",
        "AutoParts",
        "OfficePro",
        "PetLover",
        "JewelCraft",
        "FurnitureWorld",
        "BookWorm",
    ]

    # Currency codes
    CURRENCY_CODES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL"]

    # Product adjectives for name generation
    PRODUCT_ADJECTIVES = [
        "Premium",
        "Deluxe",
        "Advanced",
        "Professional",
        "Ultimate",
        "Essential",
        "Classic",
        "Modern",
        "Luxury",
        "Budget",
        "Compact",
        "Portable",
        "Wireless",
        "Smart",
        "Eco-friendly",
        "Organic",
        "Handcrafted",
        "Vintage",
        "Digital",
        "Analog",
    ]

    # Product nouns for name generation
    PRODUCT_NOUNS = {
        "ELECTRONICS": [
            "Smartphone",
            "Laptop",
            "Tablet",
            "Headphones",
            "Camera",
            "TV",
            "Speaker",
            "Smartwatch",
            "Router",
            "Drone",
        ],
        "CLOTHING": ["Shirt", "Pants", "Dress", "Jacket", "Sweater", "Socks", "Hat", "Gloves", "Scarf", "Shoes"],
        "HOME_GOODS": ["Pillow", "Blanket", "Lamp", "Rug", "Curtains", "Vase", "Frame", "Clock", "Mirror", "Candle"],
        "BEAUTY": [
            "Lipstick",
            "Foundation",
            "Mascara",
            "Eyeshadow",
            "Perfume",
            "Lotion",
            "Serum",
            "Cleanser",
            "Brush",
            "Nail Polish",
        ],
        "HEALTH": [
            "Vitamin",
            "Supplement",
            "Massager",
            "Thermometer",
            "Bandage",
            "Cream",
            "Inhaler",
            "Monitor",
            "Scale",
            "Brace",
        ],
        "SPORTS": ["Ball", "Racket", "Weights", "Mat", "Helmet", "Gloves", "Shoes", "Jersey", "Bag", "Bottle"],
        "TOYS": [
            "Doll",
            "Action Figure",
            "Puzzle",
            "Game",
            "Blocks",
            "Car",
            "Plush",
            "Robot",
            "Craft Kit",
            "Board Game",
        ],
        "BOOKS": [
            "Novel",
            "Textbook",
            "Cookbook",
            "Biography",
            "Journal",
            "Comic",
            "Dictionary",
            "Guide",
            "Atlas",
            "Encyclopedia",
        ],
        "FOOD": ["Chocolate", "Snack", "Pasta", "Sauce", "Cereal", "Spice", "Oil", "Nuts", "Chips", "Candy"],
        "BEVERAGES": ["Coffee", "Tea", "Juice", "Soda", "Water", "Wine", "Beer", "Smoothie", "Energy Drink", "Milk"],
        "AUTOMOTIVE": ["Oil", "Filter", "Wax", "Cleaner", "Tool", "Cover", "Charger", "Mount", "Light", "Mat"],
        "OFFICE_SUPPLIES": [
            "Pen",
            "Notebook",
            "Stapler",
            "Folder",
            "Paper",
            "Tape",
            "Scissors",
            "Calculator",
            "Marker",
            "Envelope",
        ],
        "PET_SUPPLIES": ["Food", "Toy", "Bed", "Collar", "Leash", "Brush", "Bowl", "Treat", "Carrier", "Shampoo"],
        "JEWELRY": [
            "Ring",
            "Necklace",
            "Bracelet",
            "Earrings",
            "Watch",
            "Pendant",
            "Brooch",
            "Cufflinks",
            "Anklet",
            "Tiara",
        ],
        "FURNITURE": ["Chair", "Table", "Sofa", "Bed", "Desk", "Shelf", "Cabinet", "Dresser", "Stool", "Bookcase"],
    }

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        min_price: float = 0.99,
        max_price: float = 9999.99,
        dataset: str | None = None,
    ):
        """Initialize the ProductEntity.

        Args:
            class_factory_util: The class factory utility instance
            locale: Locale code for localization
            min_price: Minimum product price
            max_price: Maximum product price
            dataset: Optional dataset name
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._min_price = min_price
        self._max_price = max_price

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "product_id": self._generate_product_id,
                "name": self._generate_name,
                "description": self._generate_description,
                "price": self._generate_price,
                "category": self._generate_category,
                "brand": self._generate_brand,
                "sku": self._generate_sku,
                "condition": self._generate_condition,
                "availability": self._generate_availability,
                "currency": self._generate_currency,
                "weight": self._generate_weight,
                "dimensions": self._generate_dimensions,
                "color": self._generate_color,
                "rating": self._generate_rating,
                "tags": self._generate_tags,
            }
        )

    def _generate_product_id(self) -> str:
        """Generate a unique product ID."""
        return f"PROD-{uuid.uuid4().hex[:10].upper()}"

    def _generate_category(self) -> str:
        """Generate a random product category."""
        return random.choice(self.PRODUCT_CATEGORIES)

    def _generate_name(self) -> str:
        """Generate a product name based on category."""
        category = self.category
        adjective = random.choice(self.PRODUCT_ADJECTIVES)
        noun = random.choice(self.PRODUCT_NOUNS.get(category, ["Product"]))
        brand = self.brand

        # Different name patterns
        patterns = [
            f"{brand} {adjective} {noun}",
            f"{adjective} {noun} by {brand}",
            f"{brand} {noun}",
            f"{adjective} {brand} {noun}",
        ]

        return random.choice(patterns)

    def _generate_description(self) -> str:
        """Generate a product description based on name and category."""
        name = self.name
        category = self.category

        # Features based on category
        features = {
            "ELECTRONICS": [
                "High performance",
                "Energy efficient",
                "Wireless connectivity",
                "Smart features",
                "HD display",
                "Long battery life",
            ],
            "CLOTHING": [
                "Comfortable fit",
                "Durable material",
                "Stylish design",
                "Machine washable",
                "Breathable fabric",
                "All-season wear",
            ],
            "HOME_GOODS": [
                "Modern design",
                "Easy to clean",
                "Space-saving",
                "Eco-friendly materials",
                "Handcrafted",
                "Versatile use",
            ],
            "BEAUTY": [
                "Long-lasting",
                "Dermatologist tested",
                "Cruelty-free",
                "Natural ingredients",
                "Hypoallergenic",
                "Fragrance-free",
            ],
            "HEALTH": ["Clinically proven", "All-natural", "Fast-acting", "Doctor recommended", "Non-GMO", "Vegan"],
            "SPORTS": [
                "Professional grade",
                "Lightweight",
                "Durable construction",
                "Weather-resistant",
                "Ergonomic design",
                "High performance",
            ],
            "TOYS": [
                "Educational",
                "Age-appropriate",
                "Develops motor skills",
                "Stimulates creativity",
                "Safe materials",
                "Interactive",
            ],
            "BOOKS": [
                "Bestseller",
                "Award-winning",
                "Comprehensive guide",
                "Illustrated",
                "Updated edition",
                "Easy to understand",
            ],
            "FOOD": ["Gourmet quality", "Organic", "No preservatives", "Gluten-free", "Low calorie", "Rich flavor"],
            "BEVERAGES": [
                "Refreshing taste",
                "No artificial flavors",
                "Low sugar",
                "Premium quality",
                "Sustainably sourced",
                "Bold flavor",
            ],
            "AUTOMOTIVE": [
                "High performance",
                "Easy installation",
                "Universal fit",
                "Weather-resistant",
                "Long-lasting",
                "Premium quality",
            ],
            "OFFICE_SUPPLIES": [
                "Professional quality",
                "Durable",
                "Ergonomic design",
                "Space-saving",
                "Eco-friendly",
                "Versatile use",
            ],
            "PET_SUPPLIES": [
                "Veterinarian approved",
                "Durable",
                "Easy to clean",
                "Non-toxic materials",
                "Comfortable",
                "All-natural",
            ],
            "JEWELRY": [
                "Handcrafted",
                "Premium materials",
                "Elegant design",
                "Hypoallergenic",
                "Adjustable size",
                "Gift-ready",
            ],
            "FURNITURE": [
                "Sturdy construction",
                "Easy assembly",
                "Space-saving design",
                "Comfortable",
                "Modern style",
                "Versatile use",
            ],
        }

        # Get 2-3 random features for this category
        category_features = features.get(category, ["High quality", "Versatile", "Durable"])
        selected_features = random.sample(category_features, min(len(category_features), random.randint(2, 3)))

        # Create description
        description = f"{name} - {', '.join(selected_features)}. "
        description += (
            f"This premium {category.lower().replace('_', ' ')} product offers exceptional quality and value. "
        )

        # Add random benefits
        benefits = [
            "Perfect for everyday use.",
            "Ideal for gifts and special occasions.",
            "Designed with customer satisfaction in mind.",
            "Backed by our satisfaction guarantee.",
            "One of our best-selling products.",
            "Loved by customers worldwide.",
        ]

        description += random.choice(benefits)

        return description

    def _generate_price(self) -> float:
        """Generate a random product price."""
        # Use different price points based on common retail pricing strategies
        min_price = self._min_price
        max_price = self._max_price

        price_points = [
            round(random.uniform(min_price, max_price), 2),  # Regular price
            round(random.uniform(max(min_price, 1.0), min(max_price, 100)), 99) / 100,  # $X.99 price
            round(random.uniform(max(min_price, 100), min(max_price, 1000)), 95) / 100,  # $X.95 price
            round(random.uniform(max(min_price, 1000), max_price), 0),  # Whole dollar price for expensive items
        ]

        price = random.choice(price_points)
        return max(min_price, min(price, max_price))  # Ensure price is between min_price and max_price

    def _generate_brand(self) -> str:
        """Generate a random product brand."""
        return random.choice(self.PRODUCT_BRANDS)

    def _generate_sku(self) -> str:
        """Generate a random SKU (Stock Keeping Unit)."""
        # Format: BRAND-CATEGORY-RANDOM
        brand_code = self.brand[:3].upper()
        category_code = self.category[:3].upper()
        random_code = "".join(random.choices("0123456789", k=6))

        return f"{brand_code}-{category_code}-{random_code}"

    def _generate_condition(self) -> str:
        """Generate a random product condition."""
        # Weight the conditions to make NEW more common
        weights = [0.8, 0.1, 0.05, 0.03, 0.02]  # Probabilities for each condition
        return random.choices(self.PRODUCT_CONDITIONS, weights=weights, k=1)[0]

    def _generate_availability(self) -> str:
        """Generate a random product availability."""
        # Weight the availability to make IN_STOCK more common
        weights = [0.7, 0.15, 0.1, 0.03, 0.02]  # Probabilities for each availability
        return random.choices(self.PRODUCT_AVAILABILITY, weights=weights, k=1)[0]

    def _generate_currency(self) -> str:
        """Generate a random currency code."""
        return random.choice(self.CURRENCY_CODES)

    def _generate_weight(self) -> float:
        """Generate a random product weight in kg."""
        return round(random.uniform(0.1, 50.0), 2)

    def _generate_dimensions(self) -> str:
        """Generate random product dimensions (length x width x height) in cm."""
        length = round(random.uniform(1, 200), 1)
        width = round(random.uniform(1, 200), 1)
        height = round(random.uniform(1, 200), 1)

        return f"{length} x {width} x {height} cm"

    def _generate_color(self) -> str:
        """Generate a random product color."""
        colors = [
            "Red",
            "Blue",
            "Green",
            "Yellow",
            "Black",
            "White",
            "Gray",
            "Purple",
            "Pink",
            "Orange",
            "Brown",
            "Silver",
            "Gold",
            "Navy",
            "Teal",
            "Beige",
        ]

        return random.choice(colors)

    def _generate_rating(self) -> float:
        """Generate a random product rating (1-5 stars)."""
        # Weight the ratings to make higher ratings more common
        weights = [0.05, 0.1, 0.2, 0.3, 0.35]  # Probabilities for 1-5 stars
        rating = float(random.choices([1, 2, 3, 4, 5], weights=weights, k=1)[0])

        # Add decimal precision for half-star ratings
        if random.random() < 0.5:
            rating -= 0.5

        return max(1.0, rating)  # Ensure minimum rating of 1.0

    def _generate_tags(self) -> list[str]:
        """Generate random product tags based on category and features."""
        category = self.category

        # Base tags from category
        base_tags = [category.lower().replace("_", " ")]

        # Add brand as a tag
        brand_tag = self.brand.lower()
        base_tags.append(brand_tag)

        # Add condition as a tag if not NEW
        condition = self.condition
        if condition != "NEW":
            base_tags.append(condition.lower())

        # Additional tags based on category
        category_tags = {
            "ELECTRONICS": ["tech", "gadget", "digital", "electronic", "device", "smart"],
            "CLOTHING": ["fashion", "apparel", "wear", "outfit", "style", "garment"],
            "HOME_GOODS": ["home", "decor", "household", "interior", "domestic", "living"],
            "BEAUTY": ["cosmetic", "makeup", "skincare", "beauty", "grooming", "personal care"],
            "HEALTH": ["wellness", "fitness", "health", "medical", "supplement", "care"],
            "SPORTS": ["athletic", "fitness", "exercise", "sport", "outdoor", "activity"],
            "TOYS": ["play", "game", "children", "kids", "fun", "entertainment"],
            "BOOKS": ["reading", "literature", "education", "knowledge", "learning", "publication"],
            "FOOD": ["edible", "gourmet", "cuisine", "snack", "meal", "nutrition"],
            "BEVERAGES": ["drink", "liquid", "refreshment", "hydration", "thirst", "brew"],
            "AUTOMOTIVE": ["car", "vehicle", "auto", "motor", "driving", "transport"],
            "OFFICE_SUPPLIES": ["office", "business", "professional", "work", "stationery", "desk"],
            "PET_SUPPLIES": ["pet", "animal", "companion", "care", "dog", "cat"],
            "JEWELRY": ["accessory", "ornament", "decoration", "adornment", "precious", "gem"],
            "FURNITURE": ["furnishing", "interior", "home", "decor", "living", "room"],
        }

        # Select 2-4 random tags from the category
        selected_category_tags = random.sample(
            category_tags.get(category, ["product", "item", "goods"]),
            min(len(category_tags.get(category, [])), random.randint(2, 4)),
        )

        # Combine all tags
        all_tags = base_tags + selected_category_tags

        # Add a popular/trending tag occasionally
        if random.random() < 0.2:
            trending_tags = ["bestseller", "trending", "popular", "new arrival", "limited edition", "sale"]
            all_tags.append(random.choice(trending_tags))

        return all_tags

    def reset(self) -> None:
        """Reset all field generators."""
        for generator in self._field_generators.values():
            generator.reset()

    @property
    def product_id(self) -> str:
        """Get the product ID."""
        value = self._field_generators["product_id"].get()
        assert value is not None, "product_id should not be None"
        return value

    @property
    def name(self) -> str:
        """Get the product name."""
        value = self._field_generators["name"].get()
        assert value is not None, "name should not be None"
        return value

    @property
    def description(self) -> str:
        """Get the product description."""
        value = self._field_generators["description"].get()
        assert value is not None, "description should not be None"
        return value

    @property
    def price(self) -> float:
        """Get the product price."""
        value = self._field_generators["price"].get()
        assert value is not None, "price should not be None"
        return value

    @property
    def category(self) -> str:
        """Get the product category."""
        value = self._field_generators["category"].get()
        assert value is not None, "category should not be None"
        return value

    @property
    def brand(self) -> str:
        """Get the product brand."""
        value = self._field_generators["brand"].get()
        assert value is not None, "brand should not be None"
        return value

    @property
    def sku(self) -> str:
        """Get the product SKU."""
        value = self._field_generators["sku"].get()
        assert value is not None, "sku should not be None"
        return value

    @property
    def condition(self) -> str:
        """Get the product condition."""
        value = self._field_generators["condition"].get()
        assert value is not None, "condition should not be None"
        return value

    @property
    def availability(self) -> str:
        """Get the product availability."""
        value = self._field_generators["availability"].get()
        assert value is not None, "availability should not be None"
        return value

    @property
    def currency(self) -> str:
        """Get the product currency."""
        value = self._field_generators["currency"].get()
        assert value is not None, "currency should not be None"
        return value

    @property
    def weight(self) -> float:
        """Get the product weight."""
        value = self._field_generators["weight"].get()
        assert value is not None, "weight should not be None"
        return value

    @property
    def dimensions(self) -> str:
        """Get the product dimensions."""
        value = self._field_generators["dimensions"].get()
        assert value is not None, "dimensions should not be None"
        return value

    @property
    def color(self) -> str:
        """Get the product color."""
        value = self._field_generators["color"].get()
        assert value is not None, "color should not be None"
        return value

    @property
    def rating(self) -> float:
        """Get the product rating."""
        value = self._field_generators["rating"].get()
        assert value is not None, "rating should not be None"
        return value

    @property
    def tags(self) -> list[str]:
        """Get the product tags."""
        value = self._field_generators["tags"].get()
        assert value is not None, "tags should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the product entity to a dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "brand": self.brand,
            "sku": self.sku,
            "condition": self.condition,
            "availability": self.availability,
            "currency": self.currency,
            "weight": self.weight,
            "dimensions": self.dimensions,
            "color": self.color,
            "rating": self.rating,
            "tags": self.tags,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of product entities.

        Args:
            count: Number of products to generate

        Returns:
            List of product dictionaries
        """
        field_names = list(self._field_generators.keys())
        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
