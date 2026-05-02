import csv 
from pathlib import Path 

sales=0
refunds=0
net_revenue=0
data=Path("sample_data/retail/atlanta.csv")
with data.open(mode="r",encoding="utf-8") as f:
    reader=csv.DictReader(f)

    for row in reader:
        quantity=float(row["quantity"])
        price=float(row["unit_price"])
        amount=quantity*price
        if row["transaction_type"]=="sale":
            sales+=amount
        if row["transaction_type"]=="refund":
            refunds+=abs(amount)
    net_revenue=sales-refunds

    print("Sales",sales)
    print("Refund:",refunds)
    print("Net Revenue",net_revenue)
