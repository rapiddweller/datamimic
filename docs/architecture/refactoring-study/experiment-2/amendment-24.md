# Amendment 24: separate Generate export order

Date: 2026-09-28. Astra decision during S3F2 review.

The worker calls `export_order.export_product_by_page`. Grouping that module
with `task.py` made the declared workers-to-orchestration edge cyclic because
orchestration already requires workers. Give the existing `export_order.py` its
own Generate child with one public operation; workers require it, and it has
no child dependency. The physical file and runtime behavior do not change.
