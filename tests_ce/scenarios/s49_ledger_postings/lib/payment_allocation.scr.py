# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The global part of the ledger: split each payment over the open invoices of its customer, to the cent.

A payment is split in proportion to the open amounts (L6). Each share is rounded down, then the cents that are left go,
one each, to the largest fractional parts (the largest remainder method), ties by invoice id. So the shares add up to
the payment exactly. The order is fixed (payments by date, then id), so the same inputs give the same split.
"""

from collections.abc import Mapping, Sequence
from enum import StrEnum

Row = Mapping[str, object]


class Outcome(StrEnum):
    SOLVED = "solved"
    INFEASIBLE = "infeasible"


def allocate_payments(invoices: Sequence[Row], payments: Sequence[Row]) -> dict[str, object]:
    """Return the allocation lines (``entries``), the outcome with its message and, per share, how it was rounded
    (``splits``). A payment above the open amount of its customer is infeasible: nothing is allocated."""
    open_cents = {invoice["invoice_id"]: invoice["gross_cents"] for invoice in invoices}
    entries: list[Row] = []
    splits: list[Row] = []
    for payment in sorted(payments, key=lambda payment: (payment["paid_on"], payment["payment_id"])):
        due = sorted(
            (
                invoice
                for invoice in invoices
                if invoice["customer_id"] == payment["customer_id"]
                and invoice["invoice_date"] <= payment["paid_on"]
                and open_cents[invoice["invoice_id"]] > 0
            ),
            key=lambda invoice: invoice["invoice_id"],
        )
        total_open = sum(open_cents[invoice["invoice_id"]] for invoice in due)
        if payment["amount_cents"] > total_open:
            message = (
                f"payment {payment['payment_id']} of {payment['amount_cents']} cents is above the "
                f"{total_open} cents that {payment['customer_id']} owes on {payment['paid_on']}"
            )
            return {"outcome": Outcome.INFEASIBLE.value, "message": f"no allocation exists: {message}", "entries": [], "splits": []}
        floors = {
            invoice["invoice_id"]: payment["amount_cents"] * open_cents[invoice["invoice_id"]] // total_open
            for invoice in due
        }
        fraction = {
            invoice["invoice_id"]: payment["amount_cents"] * open_cents[invoice["invoice_id"]] % total_open
            for invoice in due
        }
        extra = payment["amount_cents"] - sum(floors.values())
        winners = sorted(floors, key=lambda invoice_id: (-fraction[invoice_id], invoice_id))[:extra]
        for invoice in due:
            invoice_id = invoice["invoice_id"]
            share = floors[invoice_id] + (invoice_id in winners)
            open_cents[invoice_id] -= share
            entries.append(
                {
                    "allocation_id": f"AL{len(entries) + 1:02d}",
                    "payment_id": payment["payment_id"],
                    "invoice_id": invoice_id,
                    "amount_cents": share,
                }
            )
            splits.append(
                {
                    "payment_id": payment["payment_id"],
                    "invoice_id": invoice_id,
                    "floor_cents": floors[invoice_id],
                    "extra_cent": invoice_id in winners,
                }
            )
    return {
        "outcome": Outcome.SOLVED.value,
        "message": f"{len(payments)} payments are split over {len(entries)} invoice shares",
        "entries": entries,
        "splits": splits,
    }
