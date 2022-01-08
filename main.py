import asyncio

from data.MyDataManager import MyDataManager
from ui.MyGuiManager import MyGuiManager
from work.TranferMoney import TransferMoney


async def main():
    myGui = await MyGuiManager.createIns()

    dataManager = await MyDataManager.createIns()
    myGui.setDataManager(dataManager)

    transferMoney = await TransferMoney.createIns(dataManager)
    myGui.setTransferMoney(transferMoney)

    while True:
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
