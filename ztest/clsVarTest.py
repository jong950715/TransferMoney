class ClaA:
    var1 = False

    def __init__(self):
        #self.var1 = True
        pass

    @classmethod
    def getVar(cls):
        return cls.var1

    def pr(self):
        print(self.var1)



insA = ClaA()
print(insA)
print(ClaA.getVar())
insA.pr()