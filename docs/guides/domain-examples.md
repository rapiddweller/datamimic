# Domain examples

This page moved from the README. Each example uses a seed, so the values repeat.

## Patient model with an age range

```xml
<setup rngSeed="42">
  <generate name="patients" count="1000" target="CSV">
    <variable name="patient" entity="Patient" dataset="US" ageMin="60" ageMax="80" />
    <key name="full_name"   script="patient.full_name" />
    <key name="age"         script="patient.age" />
    <array name="conditions" script="patient.conditions" />
  </generate>
</setup>
```

Run it with `datamimic run <project>/datamimic.xml`. Patient conditions are weighted by age.

## Bank account service

```python
import random
from datamimic_ce.domains.finance.services import BankAccountService

account = BankAccountService(rng=random.Random(42)).generate()
print(account.account_number, account.balance)
```
