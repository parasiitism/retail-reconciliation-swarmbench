# Canonical Data Model

The platform should not hardcode one domain like retail.

Instead, normalize every source row into a flexible canonical record.

## Canonical Record Shape

```text
record_id
source
entity_id
event_date
record_type
amount
quantity
currency
category
status
metadata
```

## Field Meaning

- `record_id`: unique ID from source system
- `source`: source filename or system name
- `entity_id`: customer, patient, account, product, or shipment identifier
- `event_date`: transaction, claim, invoice, or shipment date
- `record_type`: sale, refund, claim, payment, invoice, shipment, adjustment
- `amount`: normalized numeric amount
- `quantity`: normalized quantity when applicable
- `currency`: INR, USD, etc.
- `category`: product category, claim type, ledger account, shipment class
- `status`: paid, pending, denied, returned, settled, etc.
- `metadata`: domain-specific fields that do not fit the common schema

## Learning Task

Before writing code, create three sample rows by hand:

1. Retail sale
2. Finance payment
3. Healthcare claim

Map each one into this canonical model.
