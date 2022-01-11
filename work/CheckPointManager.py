import pickle
from enum import Enum


class ExitCode(Enum):
    RUNNING = 'running',
    GOOD = 'good'


class CheckPointManager:
    """
    피클은 바이너리를 다루기때문에 속도가 갱장히 빠름빠름~
    """
    def __init__(self):
        self.pickleList = []
        self.pickleFile = ''
        self.exitCode = ExitCode.RUNNING

    def saveCheckPoint(self):
        self.exitCode = ExitCode.RUNNING
        self._savePickle()

    def saveGoodExitPoint(self):
        self.exitCode = ExitCode.GOOD
        self._savePickle()

    def checkUnPredictedExit(self):
        if self.isSuccessfulExit() == False:
            self._loadPickle()
        self.exitCode = ExitCode.RUNNING

    def isSuccessfulExit(self):
        exitCode = self._getAttrInPickle('exitCode')
        if exitCode == None:
            return True  # 문제 없음. (저장된 pickle 이 없는 경우)
        if exitCode == ExitCode.GOOD:
            return True  # 문제 없음. 잘 종료된 경우
        if exitCode == ExitCode.RUNNING:
            return False  # 문제!! 동작중 의도치 않게 종료된 경우

        raise Exception('설계를 잘못했나? 올 수 없는 경로임.')

    def _setPickleFile(self, pF):
        self.pickleFile = pF

    def _setPickleList(self, pL):
        pL = set(pL)
        pL.add('exitCode')
        self.pickleList = pL

    def _loadPickle(self):
        with open(self.pickleFile, 'rb') as f:
            self._loads(f.read())

    def _savePickle(self):
        with open(self.pickleFile, 'wb') as f:
            f.write(self._dumps())

    def _dumps(self):
        res = {}
        for var in self.pickleList:
            res[var] = getattr(self, var)

        return pickle.dumps(res)

    def _loads(self, pickledData):
        pickledData = pickle.loads(pickledData)
        for var in self.pickleList:
            setattr(self, var, pickledData[var])

    def _getAttrInPickle(self, attr):
        try:
            with open(self.pickleFile, 'rb') as f:
                pickledData = pickle.loads(f.read())
                return pickledData[attr]
        except (KeyError, FileNotFoundError):
            return None
        except Exception as e:
            raise e


class TestClass(CheckPointManager):
    def __init__(self):
        self._setPickleFile('testPickle.pickle')
        self._setPickleList(['var1', 'var2'])
        self.var1 = 'text1'
        self.var2 = 'text2'

        self.checkUnPredictedExit()

    def task1(self):
        self.var1 = 'task1 Doing'
        self.saveCheckPoint()

    def task2(self):
        self.var2 = 'task2 Doing'
        self.saveCheckPoint()

    def task3(self):
        self.var1 = 'task1 Done'
        self.var2 = 'task2 Done'
        self.saveGoodExitPoint()

    def pr(self):
        print(self.var1, '\t\t\t', self.var2)


def testCode():
    ins = TestClass()
    ins.pr()

    ins.task1()
    ins.pr()

    ins = TestClass()
    ins.pr()

    ins.task2()
    ins.pr()

    ins.task3() # 여기 주석처리하면? 달라짐
    ins.pr() #

    '''
    text1      text2
    task1 Doing      text2
    task1 Doing      text2
    task1 Doing      task2 Doing
    task1 Done      task2 Done
    
    '''


if __name__ == '__main__':
    testCode()
