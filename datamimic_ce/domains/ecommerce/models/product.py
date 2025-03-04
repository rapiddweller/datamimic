# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product model.

This module provides a model for representing an e-commerce product.
"""

import random
import uuid
from typing import Any, ClassVar, Dict, List, Optional, cast

from datamimic_ce.core.base_entity import BaseEntity
from datamimic_ce.core.property_cache import property_cache
from datamimic_ce.domains.ecommerce.data_loaders.product_loader import ProductDataLoader
from datamimic_ce.domains.ecommerce.utils.random_utils import (
    generate_id,
    get_property_values_by_category,
    price_with_strategy,
    weighted_choice,
)


class Product(BaseEntity):
    """Model for representing an e-commerce product.

    This class provides a model for generating realistic product data including
    product IDs, names, descriptions, prices, categories, and other product attributes.
    """

    # Category-specific features for product descriptions
    _FEATURES_BY_CATEGORY: ClassVar[Dict[str, List[str]]] = {
        "ELECTRONICS": [
            "High performance",
            "Energy efficient",
            "Wireless connectivity",
            "Smart features",
            "HD display",
            "Long battery life",
            "Touch screen",
            "Ultra-lightweight",
            "Voice control",
            "Water resistant",
        ],
        "CLOTHING": [
            "Comfortable fit",
            "Durable material",
            "Stylish design",
            "Machine washable",
            "Breathable fabric",
            "All-season wear",
            "Moisture-wicking",
            "Wrinkle-resistant",
            "Stain-resistant",
            "UV protection",
        ],
        "HOME_GOODS": [
            "Modern design",
            "Easy to clean",
            "Space-saving",
            "Eco-friendly materials",
            "Handcrafted",
            "Versatile use",
            "Durable construction",
            "Stain-resistant",
            "Hypoallergenic",
            "Multi-functional",
        ],
        "BEAUTY": [
            "Long-lasting",
            "Dermatologist tested",
            "Cruelty-free",
            "Natural ingredients",
            "Hypoallergenic",
            "Fragrance-free",
            "Non-comedogenic",
            "Paraben-free",
            "Vegan",
            "Oil-free",
        ],
        "HEALTH": [
            "Clinically proven",
            "All-natural",
            "Fast-acting",
            "Doctor recommended",
            "Non-GMO",
            "Vegan",
            "Gluten-free",
            "Organic",
            "Sugar-free",
            "No artificial flavors",
        ],
        "SPORTS": [
            "Professional grade",
            "Lightweight",
            "Durable construction",
            "Weather-resistant",
            "Ergonomic design",
            "High performance",
            "Quick-dry material",
            "Impact-resistant",
            "Adjustable fit",
            "Non-slip grip",
        ],
        "TOYS": [
            "Educational",
            "Age-appropriate",
            "Develops motor skills",
            "Stimulates creativity",
            "Safe materials",
            "Interactive",
            "Battery-operated",
            "BPA-free",
            "Washable",
            "Encourages learning",
        ],
        "BOOKS": [
            "Bestseller",
            "Award-winning",
            "Comprehensive guide",
            "Illustrated",
            "Updated edition",
            "Easy to understand",
            "Well-researched",
            "Critically acclaimed",
            "First edition",
            "Includes index",
        ],
        "FOOD": [
            "Gourmet quality",
            "Organic",
            "No preservatives",
            "Gluten-free",
            "Low calorie",
            "Rich flavor",
            "Fresh ingredients",
            "Locally sourced",
            "High protein",
            "Low sugar",
        ],
        "BEVERAGES": [
            "Refreshing taste",
            "No artificial flavors",
            "Low sugar",
            "Premium quality",
            "Sustainably sourced",
            "Bold flavor",
            "Naturally sweetened",
            "No added sugar",
            "Fair trade certified",
            "Low calorie",
        ],
        "AUTOMOTIVE": [
            "High performance",
            "Easy installation",
            "Universal fit",
            "Weather-resistant",
            "Long-lasting",
            "Premium quality",
            "OEM compatible",
            "Heavy-duty",
            "Rust-resistant",
            "UV protected",
        ],
        "OFFICE_SUPPLIES": [
            "Professional quality",
            "Durable",
            "Ergonomic design",
            "Space-saving",
            "Eco-friendly",
            "Versatile use",
            "Archival quality",
            "Smudge-resistant",
            "Precision engineered",
            "Refillable",
        ],
        "PET_SUPPLIES": [
            "Veterinarian approved",
            "Durable",
            "Easy to clean",
            "Non-toxic materials",
            "Comfortable",
            "All-natural",
            "Chew-resistant",
            "Hypoallergenic",
            "Eco-friendly",
            "Machine washable",
        ],
        "JEWELRY": [
            "Handcrafted",
            "Premium materials",
            "Elegant design",
            "Hypoallergenic",
            "Adjustable size",
            "Gift-ready",
            "Tarnish-resistant",
            "Ethically sourced",
            "Limited edition",
            "Water-resistant",
        ],
        "FURNITURE": [
            "Sturdy construction",
            "Easy assembly",
            "Space-saving design",
            "Comfortable",
            "Modern style",
            "Versatile use",
            "Stain-resistant",
            "Water-resistant",
            "Scratch-resistant",
            "Eco-friendly materials",
        ],
    }

    # General benefits for product descriptions
    _BENEFITS: ClassVar[List[str]] = [
        "Perfect for everyday use.",
        "Ideal for gifts and special occasions.",
        "Designed with customer satisfaction in mind.",
        "Backed by our satisfaction guarantee.",
        "One of our best-selling products.",
        "Loved by customers worldwide.",
        "Exceptional value for the price.",
        "Guaranteed to exceed expectations.",
        "Makes a perfect addition to any collection.",
        "Industry-leading quality and performance.",
    ]

    # Product colors
    _COLORS: ClassVar[List[str]] = [
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
        "Burgundy",
        "Turquoise",
        "Olive",
        "Maroon",
    ]

    def __init__(
        self,
        locale: str = "en",
        min_price: float = 0.99,
        max_price: float = 9999.99,
        dataset: Optional[str] = None,
    ):
        """Initialize the Product model.

        Args:
            locale: Locale code for localization
            min_price: Minimum product price
            max_price: Maximum product price
            dataset: Optional dataset code (country code)
        """
        super().__init__(locale, dataset)
        self._min_price = min_price
        self._max_price = max_price
        self._dataset = dataset

        # Initialize cached properties
        self._product_id = None
        self._name = None
        self._description = None
        self._price = None
        self._category = None
        self._brand = None
        self._sku = None
        self._condition = None
        self._availability = None
        self._currency = None
        self._weight = None
        self._dimensions = None
        self._color = None
        self._rating = None
        self._tags = None

    @property
    def product_id(self) -> str:
        """Get the product ID.

        Returns:
            A unique product ID
        """
        if self._product_id is None:
            self._product_id = generate_id("PROD", 8)
        return self._product_id

    @property
    def category(self) -> str:
        """Get the product category.

        Returns:
            A product category
        """
        if self._category is None:
            categories = ProductDataLoader.get_product_categories(self._dataset)
            self._category = weighted_choice(categories)
        return self._category

    @property
    def brand(self) -> str:
        """Get the product brand.

        Returns:
            A product brand
        """
        if self._brand is None:
            brands = ProductDataLoader.get_product_brands(self._dataset)
            self._brand = weighted_choice(brands)
        return self._brand

    @property
    def name(self) -> str:
        """Get the product name.

        Returns:
            A product name based on category and brand
        """
        if self._name is None:
            # Get the category and adjective
            category = self.category
            
            # Get adjectives and choose one
            adjectives = ProductDataLoader.get_product_adjectives(self._dataset)
            adjective = weighted_choice(adjectives)
            
            # Get product nouns for this category
            product_nouns = ProductDataLoader.get_product_nouns(category, self._dataset)
            if not product_nouns:
                # If no specific nouns for this category, use a generic "Product"
                noun = "Product"
            else:
                noun = weighted_choice(product_nouns)
            
            # Use the brand
            brand = self.brand
            
            # Different name patterns
            patterns = [
                f"{brand} {adjective} {noun}",
                f"{adjective} {noun} by {brand}",
                f"{brand} {noun}",
                f"{adjective} {brand} {noun}",
            ]
            
            self._name = random.choice(patterns)
        
        return self._name

    @property
    def description(self) -> str:
        """Get the product description.

        Returns:
            A detailed product description
        """
        if self._description is None:
            name = self.name
            category = self.category
            
            # Get category features
            category_features = self._FEATURES_BY_CATEGORY.get(category, ["High quality", "Versatile", "Durable"])
            selected_features = random.sample(category_features, min(len(category_features), random.randint(2, 3)))
            
            # Create description
            description = f"{name} - {', '.join(selected_features)}. "
            description += f"This premium {category.lower().replace('_', ' ')} product offers exceptional quality and value. "
            
            # Add random benefit
            description += random.choice(self._BENEFITS)
            
            self._description = description
        
        return self._description

    @property
    def price(self) -> float:
        """Get the product price.

        Returns:
            A realistic product price
        """
        if self._price is None:
            self._price = price_with_strategy(self._min_price, self._max_price)
        return self._price

    @property
    def sku(self) -> str:
        """Get the product SKU.

        Returns:
            A Stock Keeping Unit identifier
        """
        if self._sku is None:
            # Format: BRAND-CATEGORY-RANDOM
            brand_code = self.brand[:3].upper()
            category_code = self.category[:3].upper()
            random_code = "".join(random.choices("0123456789", k=6))
            
            self._sku = f"{brand_code}-{category_code}-{random_code}"
        
        return self._sku

    @property
    def condition(self) -> str:
        """Get the product condition.

        Returns:
            A product condition (e.g., NEW, USED)
        """
        if self._condition is None:
            conditions = ProductDataLoader.get_product_conditions(self._dataset)
            self._condition = weighted_choice(conditions)
        return self._condition

    @property
    def availability(self) -> str:
        """Get the product availability.

        Returns:
            A product availability status (e.g., IN_STOCK)
        """
        if self._availability is None:
            availability_options = ProductDataLoader.get_product_availability(self._dataset)
            self._availability = weighted_choice(availability_options)
        return self._availability

    @property
    def currency(self) -> str:
        """Get the product currency.

        Returns:
            A currency code (e.g., USD)
        """
        if self._currency is None:
            currencies = ProductDataLoader.get_currencies(self._dataset)
            self._currency = weighted_choice(currencies)
        return self._currency

    @property
    def weight(self) -> float:
        """Get the product weight in kg.

        Returns:
            A realistic product weight
        """
        if self._weight is None:
            # Generate weight based on category
            category = self.category
            
            # Define weight ranges by category
            weight_ranges = {
                "ELECTRONICS": (0.1, 20.0),
                "CLOTHING": (0.1, 2.0),
                "HOME_GOODS": (0.2, 30.0),
                "BEAUTY": (0.05, 1.0),
                "HEALTH": (0.05, 2.0),
                "SPORTS": (0.1, 25.0),
                "TOYS": (0.1, 10.0),
                "BOOKS": (0.2, 3.0),
                "FOOD": (0.05, 5.0),
                "BEVERAGES": (0.2, 10.0),
                "AUTOMOTIVE": (0.1, 50.0),
                "OFFICE_SUPPLIES": (0.05, 5.0),
                "PET_SUPPLIES": (0.1, 15.0),
                "JEWELRY": (0.01, 0.5),
                "FURNITURE": (1.0, 100.0),
            }
            
            min_weight, max_weight = weight_ranges.get(category, (0.1, 50.0))
            self._weight = round(random.uniform(min_weight, max_weight), 2)
        
        return self._weight

    @property
    def dimensions(self) -> str:
        """Get the product dimensions.

        Returns:
            Product dimensions in the format "length x width x height cm"
        """
        if self._dimensions is None:
            # Generate dimensions based on category
            category = self.category
            
            # Define dimension ranges by category (min/max for length, width, height)
            dimension_ranges = {
                "ELECTRONICS": ((5, 100), (5, 80), (1, 30)),
                "CLOTHING": ((20, 60), (15, 40), (1, 5)),
                "HOME_GOODS": ((10, 150), (10, 100), (5, 80)),
                "BEAUTY": ((3, 20), (3, 10), (3, 15)),
                "HEALTH": ((3, 20), (3, 15), (3, 10)),
                "SPORTS": ((5, 200), (5, 80), (5, 50)),
                "TOYS": ((5, 60), (5, 40), (5, 30)),
                "BOOKS": ((15, 30), (10, 25), (1, 5)),
                "FOOD": ((5, 30), (5, 20), (5, 20)),
                "BEVERAGES": ((5, 30), (5, 30), (10, 40)),
                "AUTOMOTIVE": ((5, 100), (5, 60), (2, 30)),
                "OFFICE_SUPPLIES": ((5, 40), (5, 30), (1, 20)),
                "PET_SUPPLIES": ((10, 100), (10, 60), (5, 50)),
                "JEWELRY": ((1, 15), (1, 15), (1, 5)),
                "FURNITURE": ((30, 200), (30, 150), (30, 100)),
            }
            
            length_range, width_range, height_range = dimension_ranges.get(category, ((1, 200), (1, 200), (1, 200)))
            
            length = round(random.uniform(length_range[0], length_range[1]), 1)
            width = round(random.uniform(width_range[0], width_range[1]), 1)
            height = round(random.uniform(height_range[0], height_range[1]), 1)
            
            self._dimensions = f"{length} x {width} x {height} cm"
        
        return self._dimensions

    @property
    def color(self) -> str:
        """Get the product color.

        Returns:
            A color name
        """
        if self._color is None:
            self._color = random.choice(self._COLORS)
        return self._color

    @property
    def rating(self) -> float:
        """Get the product rating.

        Returns:
            A rating between 1.0 and 5.0
        """
        if self._rating is None:
            # Weight the ratings to make higher ratings more common
            weights = [0.05, 0.1, 0.2, 0.3, 0.35]  # Probabilities for 1-5 stars
            rating = float(random.choices([1, 2, 3, 4, 5], weights=weights, k=1)[0])
            
            # Add decimal precision for half-star ratings
            if random.random() < 0.5:
                rating -= 0.5
            
            self._rating = max(1.0, rating)  # Ensure minimum rating of 1.0
        
        return self._rating

    @property_cache
    def tags(self) -> List[str]:
        """Get the product tags.

        Returns:
            A list of relevant tags for the product
        """
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
        """Reset all cached values."""
        self._product_id = None
        self._name = None
        self._description = None
        self._price = None
        self._category = None
        self._brand = None
        self._sku = None
        self._condition = None
        self._availability = None
        self._currency = None
        self._weight = None
        self._dimensions = None
        self._color = None
        self._rating = None
        if hasattr(self.tags, "reset_cache"):
            self.tags.reset_cache(self)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the product to a dictionary.

        Returns:
            A dictionary representation of the product
        """
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