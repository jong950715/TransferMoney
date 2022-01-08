from decimal import Decimal

s = '{:.2g}'.format(Decimal(100.12345))
s = '%s' % float('%.5g' % Decimal(100.12345))
s = '%s' % float('%.5g' % Decimal(0.0000123456))

i = Decimal(0.0123456)
print('{:g}'.format(float('{:.3g}'.format(i))))
s = '{:.3g}'.format(i)
print(s)

print('{:,}'.format(123123123123.123123))