The file `fixtures/orders.csv` holds six orders. It is a comma-separated text file with a header row. Its columns are `order_id`, `customer_id`, `status` and `total_cents`.

Write all six orders to a JSON file, as a dataset named `priced_orders`. Each JSON object has exactly these fields:

- `order_id`, copied from the file;
- `customer_id`, copied from the file;
- `total_cents`, copied from the file as a whole number;
- `priority`, the text `high` when `total_cents` is 5000 or more, and `standard` otherwise.

Do not write the `status` column. Do not change the file. Use seed `51110`.
