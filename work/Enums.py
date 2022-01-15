from enum import Enum


class TransferDir(Enum):
    UpToBn = 'Up -> Bn'
    BnToUp = 'Bn -> Up'

    def __str__(self):
        return self.value


class TransferState(Enum):
    PREPARING = 'PREPARING'
    STANDBY = 'STANDBY'
    BUYING = 'BUYING'
    TRANSFERRING = 'TRANSFERRING'
    SELLING = 'SELLING'
    DONE = 'DONE'

    def __str__(self):
        return self.value
