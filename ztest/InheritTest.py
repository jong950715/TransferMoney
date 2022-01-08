class ClassParent:
    def __init__(self, pa, pb, pc):
        self.pa = pa
        self.pb = pb
        self.pc = pc

    def printParent(self):
        print(self.pa, self.pb, self.pc)


class ClassChild(ClassParent):
    def __init__(self, *args, **kwargs):
        print(kwargs['pd'])
        super(ClassChild, self).__init__(*args, **kwargs)


insP = ClassParent(1, 2, 3)
insP.printParent()

insC = ClassChild(pa = 1, pb = 2, pc = 3, pd = 4)
insC.printParent()
