# Domain Profiles

Domain profiles are configuration files or dictionaries that teach the platform how to interpret different industries.

## Retail Profile

Should define aliases for:

- transaction ID
- SKU
- quantity
- unit price
- transaction type
- refund indicators

## Finance Profile

Should define aliases for:

- transaction ID
- account ID
- debit
- credit
- amount
- settlement date
- reversal indicators

## Healthcare Profile

Should define aliases for:

- claim ID
- patient ID
- provider ID
- claim amount
- paid amount
- service date
- denial or adjustment indicators

## Supply Chain Profile

Should define aliases for:

- shipment ID
- order ID
- SKU
- warehouse
- quantity shipped
- invoice amount
- delivery status

## Learning Task

Write domain profiles in plain English first.

Only after that, convert them into Python dictionaries or YAML files.
