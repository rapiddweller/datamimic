# Weighted Distributions in DATAMIMIC

One of the key differentiators of DATAMIMIC's Domain-Driven Framework compared to other synthetic data libraries is its use of weighted distributions that accurately reflect real-world frequencies. This document explains how this system works and its benefits.

> **Note**: This documentation focuses specifically on the weighted distribution system within DATAMIMIC's Domain-Driven Framework. DATAMIMIC offers many additional capabilities beyond what is documented here.

## The Problem with Random Data

Traditional synthetic data generators typically use uniform random distributions, where each possible value has an equal probability of being selected. While this approach is simple to implement, it produces unrealistic data that doesn't match real-world patterns.

For example, a random blood type generator might select each blood type with equal probability:

```python
# Uniform random selection (unrealistic)
blood_type = random.choice(["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"])
```

This would result in each blood type having a 12.5% frequency in the generated data. However, in reality, blood types have very different frequencies in the population, with O+ being the most common (around 38% in the US) and AB- being the rarest (around 1%).

## DATAMIMIC's Weighted Distribution Approach

DATAMIMIC addresses this problem by using weighted distributions based on real-world data. The framework loads distribution data from reference files and uses weighted random selection to generate values according to their actual frequencies.

### Example: Blood Type Distribution

In DATAMIMIC, blood types are distributed according to their real frequencies:

From `datamimic_ce/domain_data/healthcare/medical/blood_types_US.csv`:
```
O+, 38
A+, 34
B+, 9
AB+, 3
O-, 7
A-, 6
B-, 2
AB-, 1
```

A generator using this distribution would produce:
- O+ blood type 38% of the time
- A+ blood type 34% of the time
- B+ blood type 9% of the time
- And so on...

The resulting dataset has the same statistical properties as real-world data.

## Implementation Details

### Literal Generators

Literal generators are the building blocks of DATAMIMIC's weighted distribution system. Each generator is responsible for producing values of a specific type according to configured distributions.

For example, the `GenderGenerator` class:

```python
class GenderGenerator(BaseLiteralGenerator):
    def __init__(self, female_quota: float = None, other_gender_quota: float = None):
        # Calculate distributions
        female_quota, male_quota, other_gender_quota = self._calculate_gender_rate(
            female_quota, other_gender_quota
        )
        self._wgt = [female_quota, male_quota, other_gender_quota]
        self._values = ["female", "male", "other"]
        
    def generate(self) -> str:
        # Use weighted random choice
        return random.choices(self._values, weights=self._wgt, k=1)[0]
```

### Data-Driven Distributions

Many distributions are loaded from reference data files:

```python
class MedicalConditionGenerator(BaseLiteralGenerator):
    def __init__(self, dataset: str = "US"):
        self._dataset = dataset
        # Load distribution data from CSV
        self._data = self._load_distribution_data(f"healthcare/medical/medical_conditions_{dataset}.csv")
        
    def generate(self) -> str:
        # Select based on weighted distribution
        return weighted_choice(self._data)
        
    def generate_multiple(self, count: int = 3) -> list[str]:
        # Generate multiple unique conditions
        return weighted_choice_multiple(self._data, count)
```

### Conditional Distributions

DATAMIMIC also supports conditional distributions where the probability of one value depends on other values. For example, medical conditions might be correlated with age or gender:

```python
def generate_conditions(age: int, gender: str) -> list[str]:
    # Base conditions list
    conditions = []
    
    # Adjust probability based on age
    if age > 60:
        # Higher probability of age-related conditions
        if random.random() < 0.4:
            conditions.append("Hypertension")
        if random.random() < 0.3:
            conditions.append("Type 2 Diabetes")
    
    # Adjust probability based on gender
    if gender == "female":
        if random.random() < 0.1:
            conditions.append("Osteoporosis")
    
    # Add other random conditions
    num_other_conditions = weighted_choice({
        0: 0.5,  # 50% chance of no additional conditions
        1: 0.3,  # 30% chance of 1 additional condition
        2: 0.15, # 15% chance of 2 additional conditions
        3: 0.05  # 5% chance of 3 additional conditions
    })
    
    # Add other conditions from weighted distribution
    if num_other_conditions > 0:
        other_conditions = weighted_choice_multiple(
            medical_condition_distribution, 
            num_other_conditions
        )
        conditions.extend(other_conditions)
    
    return conditions
```

## Distribution Types

DATAMIMIC supports several types of distributions:

### 1. Discrete Weighted Distributions

For categorical data like blood types, genders, or medical conditions:

```python
# Example: Industry distribution for companies
INDUSTRY_DISTRIBUTION = {
    "Technology": 0.15,
    "Healthcare": 0.12,
    "Finance": 0.10,
    "Retail": 0.14,
    "Manufacturing": 0.13,
    "Education": 0.08,
    "Entertainment": 0.07,
    "Agriculture": 0.05,
    "Energy": 0.06,
    "Transportation": 0.05,
    "Construction": 0.05
}
```

### 2. Continuous Distributions

For numerical data like age, income, or transaction amounts:

```python
# Normal distribution for age
def generate_age(mean=40, stddev=15, min_age=18, max_age=90):
    age = int(random.normalvariate(mean, stddev))
    return max(min_age, min(max_age, age))

# Log-normal distribution for income
def generate_income(median=65000, sigma=0.75, min_income=20000):
    income = random.lognormvariate(math.log(median), sigma)
    return max(min_income, round(income, -3))  # Round to nearest thousand
```

### 3. Geospatial Distributions

For location-based data like addresses or GPS coordinates:

```python
# Postal code distribution based on population density
def generate_postal_code(state):
    postal_codes = state_postal_code_data[state]
    # Select based on population weights
    return weighted_choice(postal_codes)
```

### 4. Temporal Distributions

For time-based data like birthdates or transaction times:

```python
# Distribution of transactions throughout the day
HOURLY_TRANSACTION_DISTRIBUTION = {
    # Hour: probability
    0: 0.01,  # Midnight
    1: 0.005,
    # ...
    8: 0.05,  # Morning rush
    9: 0.07,
    # ...
    12: 0.08,  # Lunch time
    # ...
    17: 0.09,  # Evening rush
    18: 0.10,
    # ...
    23: 0.03   # Late night
}
```

## Benefits of Weighted Distributions

Using weighted distributions provides several key benefits:

1. **Statistical Realism**: Generated data matches the statistical properties of real-world data
2. **Improved Testing**: Edge cases appear with their natural frequency
3. **Better Visualizations**: Charts and graphs look like they're from real data
4. **Realistic Scenarios**: Business scenarios reflect actual probabilities
5. **More Effective Training Data**: Machine learning models learn from realistic patterns

## Comparing Data Quality

To illustrate the difference, here's a comparison of blood type distributions:

| Blood Type | Real World | DATAMIMIC | Faker/Random |
|------------|------------|-----------|--------------|
| O+         | 38%        | 38%       | 12.5%        |
| A+         | 34%        | 34%       | 12.5%        |
| B+         | 9%         | 9%        | 12.5%        |
| AB+        | 3%         | 3%        | 12.5%        |
| O-         | 7%         | 7%        | 12.5%        |
| A-         | 6%         | 6%        | 12.5%        |
| B-         | 2%         | 2%        | 12.5%        |
| AB-        | 1%         | 1%        | 12.5%        |

## Customizing Distributions

DATAMIMIC allows you to customize distributions to match specific requirements:

```python
# Adjust gender distribution
person_generator = PersonGenerator(
    female_quota=0.7,   # 70% female
    other_gender_quota=0.05  # 5% other
)

# Adjust age distribution
person_generator = PersonGenerator(
    min_age=25,   # Minimum age
    max_age=45    # Maximum age
)

# Create custom distribution
custom_distribution = {
    "Category1": 0.4,
    "Category2": 0.35,
    "Category3": 0.25
}
result = weighted_choice(custom_distribution)
```

## Conclusion

DATAMIMIC's weighted distribution system is a key feature that sets it apart from other synthetic data libraries. By generating data that follows realistic distributions, DATAMIMIC produces high-quality synthetic datasets that maintain the statistical properties of real-world data. 