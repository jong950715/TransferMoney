import asyncio
from decimal import Decimal
from enum import Enum
from tkinter import ttk
import tkinter as tk
from common.SingleTonAsyncInit import SingleTonAsyncInit
from common.createTask import createTask, RUNNING_FLAG
from data.MyDataManager import MyDataManager
from data.dataCommons import tickerToUpbitSymbol, tickerToBnSymbol
from ui.src.MyControlWindow import MyControlWindow
from ui.src.MyViewWindow import MyViewWindow, PREPARING_DATA, PREPARING_WORD
from work.Enums import TransferDir, TransferState
from work.TranferMoney import TransferMoney


class MyGuiManager(SingleTonAsyncInit):
    async def _asyncInit(self):
        self.dataManager = None
        self.transferMoney = None

        self._initGui()
        self.run()

    def setDataManager(self, dataManager: MyDataManager):
        self.dataManager = dataManager

    def setTransferMoney(self, transferMoney: TransferMoney):
        self.transferMoney = transferMoney

    def _initGui(self):
        self.root = tk.Tk()

        viewWindow = self.root
        controlWindow = tk.Toplevel(viewWindow)

        self.viewWindow = MyViewWindow(viewWindow)
        self.controlWindow = MyControlWindow(controlWindow)

        self._initControl()

    def _initControl(self):
        self.controlWindow.widgets['btnUpToBn'].config(command=self._startUpToBn)
        self.controlWindow.widgets['btnBnToUp'].config(command=self._startBnToUp)

    def _startUpToBn(self):
        notional = Decimal(self.controlWindow.widgets['entryKrw'].get())
        self.transferMoney.startTransfer(_dir=TransferDir.UpToBn, notional=notional)

    def _startBnToUp(self):
        notional = Decimal(self.controlWindow.widgets['entryUsdt'].get())
        self.transferMoney.startTransfer(_dir=TransferDir.BnToUp, notional=notional)

    def getDataByDir(self, _dir):
        # return [['ticker', Decimal('1234.5678'), Decimal('1234.5678'), Decimal('1234.5678'), Decimal('80000000'), Decimal('0.00012345678'), Decimal('0.00012345678'), 'upWit', 'bnDep']] * 5
        if self.dataManager:
            return self.dataManager.getDataByDirCached(_dir)
        else:
            return PREPARING_DATA

    async def updateGui(self):
        await self.updateView()
        await self.updateControl()
        self.root.update()

    async def updateView(self):
        u2b = self.getDataByDir(TransferDir.UpToBn)
        b2u = self.getDataByDir(TransferDir.BnToUp)

        if u2b[0][0] == PREPARING_WORD or b2u[0][0] == PREPARING_WORD:
            _u2b = u2b
            _b2u = b2u
        else:
            _u2b = [line.deepCopy() for line in u2b]
            _b2u = [line.deepCopy() for line in b2u]

        self.viewWindow.setDataUpToBn(_u2b)
        self.viewWindow.setDataBnToUp(_b2u)

    async def updateControl(self):
        if self.transferMoney:
            self.controlWindow.setState(self.transferMoney.getState())
        else:
            self.controlWindow.setState(TransferState.PREPARING)

    async def _run(self):
        while True:
            await self.updateGui()
            await asyncio.sleep(0.1)

    def run(self):
        asyncio.get_event_loop().call_soon(createTask, self._run())

    def getTransferState(self):
        if self.transferMoney:
            return self.transferMoney.getState()
        return TransferState.PREPARING


async def main():
    myGui = await MyGuiManager.createIns()
    myGui.run()
    while True:
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    print("끝")
