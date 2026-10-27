The file `fixtures/customers.ent.csv` lists customers. Its columns are `customer_id`, `name`, `tier` and `country`.
The file `fixtures/orders.ent.csv` lists orders. Its columns are `order_id`, `customer_id`, `order_date`, `amount_cents` and `channel`.
Both files are pipe-separated UTF-8 text files with a header row. A date has the form `YYYY-MM-DD`.

Write a JSON file for a dataset named `order_report`. It holds one JSON object for each order whose `amount_cents` is 1000 or more, and no object for any other order. Each JSON object has exactly these fields:

- `order_id`, copied from the order;
- `customer_id`, copied from the order;
- `customer_name`, the `name` of the customer with this `customer_id` in `fixtures/customers.ent.csv`, or the text `UNKNOWN` when that file has no such customer;
- `net_cents`, a whole number: `amount_cents` minus the discount. The discount is 10 percent of `amount_cents` for a customer of tier `GOLD`, 5 percent for tier `SILVER`, and 0 for any other tier, an empty tier and an unknown customer. Round the discount down to a whole number of cents;
- `campaign`, the text `YES` when the `order_date` is from 2026-03-01 to 2026-03-31, both days included, and the text `NO` otherwise.

Do not change the two files. Use seed `40961`.
