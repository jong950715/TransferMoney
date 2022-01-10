from decimal import Decimal

price = Decimal(100.234)
priceStep = Decimal(1)

price = priceStep * round(price / priceStep)

print(price)
print(type(price))

print('%f'%price)