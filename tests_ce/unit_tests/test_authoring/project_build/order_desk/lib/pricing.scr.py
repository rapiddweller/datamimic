"""Order pricing for the order desk."""


def order_total(quantity: int, unit_price: float) -> float:
    return round(quantity * unit_price, 2)
