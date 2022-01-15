from decimal import Decimal

qty = Decimal('-96.07')
qtyStep = Decimal('0.1')


qty = qtyStep * round(qty // qtyStep)

print(qty)