# Global counters for persistent IDs
customer_counter = 0
order_counter = 0
lineitem_counter = 0

# Aggregation tracking
current_order_total = 0.0
current_customer_total = 0.0
current_customer_orders = 0

def customer_id():
    global customer_counter
    customer_counter += 1
    return f"C{customer_counter}"

def order_id():
    global order_counter
    order_counter += 1
    return f"O{order_counter}"

def lineitem_id():
    global lineitem_counter
    lineitem_counter += 1
    return f"L{lineitem_counter}"

def add_to_order_total(price):
    global current_order_total
    current_order_total += price
    return True

def get_order_total():
    return round(current_order_total, 2)

def reset_order_total():
    global current_order_total
    current_order_total = 0.0

def add_to_customer_total(order_total):
    global current_customer_total, current_customer_orders
    current_customer_total += order_total
    current_customer_orders += 1

def get_customer_total():
    return round(current_customer_total, 2)

def get_customer_orders():
    return current_customer_orders

def reset_customer_total():
    global current_customer_total, current_customer_orders
    current_customer_total = 0.0
    current_customer_orders = 0