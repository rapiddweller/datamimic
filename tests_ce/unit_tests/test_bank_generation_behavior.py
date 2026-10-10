from random import Random

import pytest

from datamimic_ce.domains.finance.services.bank_service import BankService


@pytest.mark.parametrize(
    ("dataset", "expected", "next_random"),
    [
        (
            "DE",
            {
                "name": "Sparkasse",
                "swift_code": "SPKADE2H",
                "routing_number": "",
                "bank_code": "SPKADE2H",
                "bic": "AMODDEQ7",
                "bin": "4160",
                "customer_service_phone": "+49-6435-238747",
            },
            0.5643778061531902,
        ),
        (
            "US",
            {
                "name": "US Bank",
                "swift_code": "USBKUS44",
                "routing_number": "123103729",
                "bank_code": "USBKUS44",
                "bic": "AMODUSQ7",
                "bin": "4160",
                "customer_service_phone": "+1-978-2387475",
            },
            0.8738759467064391,
        ),
    ],
)
def test_seeded_bank_output_and_rng_state_are_stable(dataset, expected, next_random):
    rng = Random(731)
    bank = BankService(dataset=dataset, rng=rng).generate()

    assert bank.to_dict() == expected
    assert bank.to_dict() == expected
    assert rng.random() == next_random


def test_bank_property_access_order_preserves_its_seeded_values_and_rng_state():
    rng = Random(731)
    bank = BankService(dataset="DE", rng=rng).generate()

    assert [
        bank.bin,
        bank.bic,
        bank.customer_service_phone,
        bank.routing_number,
        bank.bank_code,
        bank.swift_code,
        bank.name,
    ] == [
        "8106",
        "DVYQDEQ7",
        "+49-37296-04828",
        "",
        "GENODEFF",
        "GENODEFF",
        "DZ Bank",
    ]
    assert rng.random() == 0.6726992709973326


def test_unsupported_dataset_uses_us_bank_data_but_keeps_requested_dataset():
    bank = BankService(dataset="FR", rng=Random(731)).generate()

    assert bank.name == "US Bank"
    assert bank.swift_code == "USBKUS44"
    assert bank.routing_number == "123103729"
    assert bank.bic == "AMODFRQ7"
