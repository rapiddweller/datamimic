# Enhanced Synthetic Data Generation with Multi-layer Constraints

This document describes the three-layer constraints system implemented in DATAMIMIC for comprehensive control over synthetic data generation.

## Overview

The enhanced constraints workflow consists of three distinct layers:

1. **Source Constraints**: Applied at the beginning to filter input data
2. **Mapping Rules**: Applied during processing to transform selected records
3. **Target Constraints**: Applied at the end to validate and finalize output data

These layers work together to create a powerful pipeline that ensures high-quality, consistent synthetic data that meets business requirements.

## Implementation

The implementation includes:

- New XML elements: `<sourceConstraints>`, `<mapping>`, and `<targetConstraints>`
- Rule-based conditional logic with `<rule if="condition" then="action">` syntax
- Task classes to process each constraint type

## Usage

### XML Example

```xml
<setup>
    <generate name="container" count="1">
        <generate name="synthetic_customers" count="1000" pageSize="100"
            source="script/person_data.json" cyclic="True">
            <key name="id" generator="IncrementGenerator" />
            
            <!-- Source Constraints: Filter input data -->
            <sourceConstraints>
                <rule if="age &lt; 30" then="risk_profile == 'High'" />
                <rule if="age &gt;= 30 and age &lt; 50" then="risk_profile == 'Medium'" />
                <rule if="age &gt;= 50" then="risk_profile == 'Low'" />
            </sourceConstraints>
            
            <!-- Mapping: Transform attributes based on source constraints -->
            <mapping>
                <rule if="risk_profile == 'High'" then="interest_rate = 0.15"/>
                <rule if="risk_profile == 'Medium'" then="interest_rate = 0.10"/>
                <rule if="risk_profile == 'Low'" then="interest_rate = 0.05"/>
                <!-- Additional rules for credit limits -->
                <rule if="income &gt; 100000" then="credit_limit = 50000" />
                <rule if="income &gt; 50000" then="credit_limit = 25000" />
                <rule if="income &gt; 30000" then="credit_limit = 10000" />
                <rule if="income &lt;= 30000" then="credit_limit = 5000" />
            </mapping>
            
            <!-- Target Constraints: Final validation -->
            <targetConstraints>
                <rule if="credit_limit &gt;= 25000 and interest_rate &lt;= 0.08" then="approval_status = 'Approved'" />
                <rule if="credit_limit &lt; 25000 or interest_rate &gt; 0.08" then="approval_status = 'Review'" />
                <rule if="credit_limit &lt;= 5000 and interest_rate &gt;= 0.12" then="approval_status = 'Denied'" />
            </targetConstraints>
        </generate>
    </generate>
</setup>
```

### Key Behaviors

#### 1. Source Constraints
- Filter input data based on conditions
- Assign initial categories or classifications
- Remove records that don't meet specific criteria

#### 2. Mapping Rules
- Apply transformations based on initial classification
- Set derived values based on input attributes
- Implement business rules for data generation

#### 3. Target Constraints
- Validate final generated data
- Add additional attributes based on generated values
- Ensure consistency across the entire dataset

## Benefits

- **Enhanced Control**: Fine-grained control over data generation process
- **Business Rule Integration**: Clear implementation of complex business rules
- **Data Quality**: Multiple validation layers ensure high-quality output
- **Consistency**: Ensures logical relationships between data attributes

## Technical Details

The implementation includes new model and task classes:

- `MappingStatement` and `MappingTask` for handling mapping rules
- `TargetConstraintsStatement` and `TargetConstraintsTask` for final validation
- Integration with existing `ConstraintsStatement` and `ConstraintsTask` classes

These components work together to provide a comprehensive constraints system that covers the entire synthetic data generation pipeline. 