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
from ui.src.MyViewWindow import MyViewWindow
from work.TranferMoney import TransferMoney, TransferState, TransferDir


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
        self.transferDir = TransferDir.UpToBn
        self.controlWindow.widgets['btnToggleDir'].config(command=self._toggleDir)
        self.controlWindow.widgets['btnUpToBn'].config(command=self._startTransfer)

    def _startTransfer(self):
        notional = Decimal(self.controlWindow.widgets['entryKrwStr'].get())
        self.transferMoney.startTransfer(dir=self.transferDir, notional=notional)

    def _toggleDir(self):
        if self.transferDir == TransferDir.UpToBn:
            self.transferDir = TransferDir.BnToUp
        elif self.transferDir == TransferDir.BnToUp:
            self.transferDir = TransferDir.UpToBn

        self.controlWindow.widgets['btnToggleDir'].config(text=str(self.transferDir))
        # ????.setTransDir()

    async def getUpToBnData(self):
        # return [['ticker', Decimal('1234.5678'), Decimal('1234.5678'), Decimal('1234.5678'), Decimal('80000000'), Decimal('0.00012345678'), Decimal('0.00012345678'), 'upWit', 'bnDep']] * 5
        if self.dataManager:
            return await self.dataManager.getUpToBnData()
        else:
            return [['준비중']]

    async def updateGui(self):
        await self.updateView()
        await self.updateControl()
        self.root.update()

    async def updateView(self):
        self.viewWindow.setDataUpToBn(await self.getUpToBnData())

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
