Create a repeatable dataset named `subscribers` with exactly 5 subscribers, and a second dataset named `invoices` with exactly 3 invoices for each subscriber, 15 invoices in total.

Each subscriber has:

- `subscriber_id`, a whole number that is different for every subscriber;
- `plan`, one of `BASIC`, `PLUS` or `PRO`.

Each invoice has:

- `invoice_id`, a whole number that is different for every invoice in the whole dataset;
- `subscriber_id`, the `subscriber_id` of the subscriber that owns the invoice;
- `state`, one of `OPEN`, `PAID` or `VOID`;
- `amount_cents`, a whole number from 500 to 20000, inclusive.

Use seed `30517`.
