import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return 'Decimal({})'.format(str(o))
        return super(DecimalEncoder, self).default(o)



pyData = {'decimal': Decimal('0.1'),
          'float': float(0.1),
          'fDecimal': Decimal(float('0.1'))
          }

jsData = json.dumps(pyData, cls=DecimalEncoder, indent='    ')

print(pyData)
print(jsData)

newPyData = json.loads(jsData, parse_float=Decimal)

print(newPyData)