# Finance Domain for DataMimic

This directory contains examples showing how to use the Finance domain in DataMimic to generate realistic financial data.

## Overview

The Finance domain provides models and generators for various financial entities:

- Bank Accounts
- Credit Cards
- Banking information

The domain follows a clean architecture approach with:

- **Models**: Pydantic models defining the structure of financial entities
- **Data Loaders**: Classes to load reference data from CSV files
- **Services**: Business logic for generating finance entities
- **Generators**: Classes that implement the DataMimic generator interface

## Usage

### Generating Bank Accounts

```python
from datamimic_ce.domains.finance.services.bank_account_service import BankAccountService

# Create a service for US bank accounts
service = BankAccountService(dataset="US")

# Generate a single bank account
account = service.generate_bank_account()

# Generate multiple bank accounts
accounts = service.generate_bank_accounts(count=5)

# Access account properties
print(f"Account Number: {account.account_number}")
print(f"Bank: {account.bank.name}")
print(f"Balance: {account.balance} {account.currency}")
```

### Generating Credit Cards

```python
from datamimic_ce.domains.finance.services.credit_card_service import CreditCardService

# Create a service for German credit cards
service = CreditCardService(dataset="DE")

# Generate a single credit card
card = service.generate_credit_card()

# Generate multiple credit cards
cards = service.generate_credit_cards(count=3)

# Access card properties
print(f"Card Number: {card.masked_card_number}")
print(f"Card Holder: {card.card_holder}")
print(f"Expiration: {card.expiration_date_str}")
```

### Using DataMimic Generators

```python
from datamimic_ce.domains.finance.generators.finance_generators import (
    BankAccountGenerator,
    CreditCardGenerator,
    FinanceDataGenerator,
)

# Generate comprehensive finance data
generator = FinanceDataGenerator(
    dataset="US",
    include_bank_accounts=True,
    include_credit_cards=True,
    num_bank_accounts=3,
    num_credit_cards=2,
)

finance_data = generator.generate()

# Access the generated data
print(f"ID: {finance_data['id']}")
for account in finance_data['bank_accounts']:
    print(f"Account: {account['account_number']}")
for card in finance_data['credit_cards']:
    print(f"Card: {card['masked_card_number']}")
```

## Data Files

The Finance domain uses reference data from CSV files:

- `datamimic_ce/data/finance/bank/banks_US.csv`: US bank information
- `datamimic_ce/data/finance/bank/banks_DE.csv`: German bank information
- `datamimic_ce/data/finance/credit_card/card_types_US.csv`: US credit card types
- `datamimic_ce/data/finance/credit_card/card_types_DE.csv`: German credit card types
- `datamimic_ce/data/finance/account_types_US.csv`: US bank account types
- `datamimic_ce/data/finance/account_types_DE.csv`: German bank account types

## Example Script

The `generate_finance_data.py` script demonstrates how to generate finance data with the DataMimic library:

```bash
python generate_finance_data.py
```

This will generate sample bank accounts and credit cards for both US and German datasets, 
displaying the results in the console and saving them to JSON files in the `output` directory.