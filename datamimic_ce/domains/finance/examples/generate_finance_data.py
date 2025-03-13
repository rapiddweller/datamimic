# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Generate finance data example.

This script demonstrates how to generate finance-related data using the DataMimic library.
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path to allow importing the DataMimic modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datamimic_ce.domains.finance.generators.credit_card_generators import (
    FinanceDataGenerator,
)
from datamimic_ce.domains.finance.services.bank_account_service import BankAccountService
from datamimic_ce.domains.finance.services.credit_card_service import CreditCardService


def generate_bank_accounts(count: int = 5, dataset: str = "US"):
    """Generate bank account data.

    Args:
        count: The number of bank accounts to generate
        dataset: The country code to use for data generation
    """
    print(f"\nGenerating {count} bank accounts for dataset {dataset}:")
    service = BankAccountService(dataset=dataset)
    accounts = service.generate_bank_accounts(count=count)

    for i, account in enumerate(accounts, 1):
        account_dict = account.dict()
        print(f"\nAccount {i}:")
        print(f"  Account Number: {account_dict['account_number']}")
        if account_dict["iban"]:
            print(f"  IBAN: {account_dict['iban']}")
        print(f"  Account Type: {account_dict['account_type']}")
        print(f"  Bank: {account_dict['bank']['name']}")
        print(f"  Balance: {account_dict['balance']:.2f} {account_dict['currency']}")

    # Save to JSON file
    os.makedirs("output", exist_ok=True)
    output_file = f"output/bank_accounts_{dataset}.json"
    with open(output_file, "w") as f:
        json.dump([account.dict() for account in accounts], f, indent=2, default=str)
    print(f"\nSaved bank accounts to {output_file}")


def generate_credit_cards(count: int = 5, dataset: str = "US"):
    """Generate credit card data.

    Args:
        count: The number of credit cards to generate
        dataset: The country code to use for data generation
    """
    print(f"\nGenerating {count} credit cards for dataset {dataset}:")
    service = CreditCardService(dataset=dataset)
    cards = service.generate_credit_cards(count=count)

    for i, card in enumerate(cards, 1):
        print(f"\nCard {i}:")
        print(f"  Card Number: {card.masked_card_number}")
        print(f"  Card Holder: {card.card_holder}")
        print(f"  Card Type: {card.card_type.type}")
        print(f"  Expiration Date: {card.expiration_date_str}")
        print(f"  CVV: {card.cvv}")
        print(f"  Credit Limit: ${card.credit_limit:.2f}")
        print(f"  Current Balance: ${card.current_balance:.2f}")
        print(f"  Issuing Bank: {card.bank_name}")

    # Save to JSON file
    os.makedirs("output", exist_ok=True)
    output_file = f"output/credit_cards_{dataset}.json"
    with open(output_file, "w") as f:
        cards_dict = []
        for card in cards:
            card_dict = card.dict()
            card_dict["masked_card_number"] = card.masked_card_number
            card_dict["expiration_date_str"] = card.expiration_date_str
            card_dict["is_expired"] = card.is_expired
            cards_dict.append(card_dict)
        json.dump(cards_dict, f, indent=2, default=str)
    print(f"\nSaved credit cards to {output_file}")


def generate_comprehensive_finance_data(dataset: str = "US"):
    """Generate comprehensive finance data including bank accounts and credit cards.

    Args:
        dataset: The country code to use for data generation
    """
    print(f"\nGenerating comprehensive finance data for dataset {dataset}:")
    generator = FinanceDataGenerator(
        dataset=dataset,
        include_bank_accounts=True,
        include_credit_cards=True,
        num_bank_accounts=3,
        num_credit_cards=2,
    )
    finance_data = generator.generate()

    print("\nFinance Data:")
    print(f"  ID: {finance_data['id']}")
    print(f"  Dataset: {finance_data['dataset']}")

    print(f"  Bank Accounts ({len(finance_data['bank_accounts'])}):")
    for i, account in enumerate(finance_data["bank_accounts"], 1):
        print(f"    Account {i}:")
        print(f"      Account Number: {account['account_number']}")
        if account["iban"]:
            print(f"      IBAN: {account['iban']}")
        print(f"      Account Type: {account['account_type']}")
        print(f"      Bank: {account['bank']['name']}")
        print(f"      Balance: {account['balance']:.2f} {account['currency']}")

    print(f"  Credit Cards ({len(finance_data['credit_cards'])}):")
    for i, card in enumerate(finance_data["credit_cards"], 1):
        print(f"    Card {i}:")
        print(f"      Card Number: {card['masked_card_number']}")
        print(f"      Card Holder: {card['card_holder']}")
        print(f"      Card Type: {card['card_type']['type']}")
        print(f"      Expiration Date: {card['expiration_date_str']}")
        print(f"      Credit Limit: ${card['credit_limit']:.2f}")
        print(f"      Current Balance: ${card['current_balance']:.2f}")
        print(f"      Issuing Bank: {card['bank_name']}")

    # Save to JSON file
    os.makedirs("output", exist_ok=True)
    output_file = f"output/finance_data_{dataset}.json"
    with open(output_file, "w") as f:
        json.dump(finance_data, f, indent=2, default=str)
    print(f"\nSaved comprehensive finance data to {output_file}")


def main():
    """Main function to demonstrate finance data generation."""
    print("Finance Data Generation Examples")
    print("===============================")

    # Generate bank accounts
    generate_bank_accounts(count=3, dataset="US")
    generate_bank_accounts(count=3, dataset="DE")

    # Generate credit cards
    generate_credit_cards(count=3, dataset="US")
    generate_credit_cards(count=3, dataset="DE")

    # Generate comprehensive finance data
    generate_comprehensive_finance_data(dataset="US")
    generate_comprehensive_finance_data(dataset="DE")


if __name__ == "__main__":
    main()
