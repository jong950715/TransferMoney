import asyncio

from config.MyConfigManager import MyConfigManager
from data.MyDataManager import MyDataManager
from selfLib.UpClient import UpClient
from binance import AsyncClient as BnClient
from ui.MyGuiManager import MyGuiManager
from work.OrderManager import OrderManager
from work.TranferMoney import TransferMoney


async def main():
    # layer -1
    myGui = await MyGuiManager.createIns()

    # layer 0
    configKeys = (await MyConfigManager.getIns()).getConfig('configKeys')
    upCli = UpClient(access=configKeys['upbit']['api_key'], secret=configKeys['upbit']['secret_key'])
    bnCli = await BnClient.create(configKeys['binance']['api_key'], configKeys['binance']['secret_key'])

    # layer 0.5
    dataManager = await MyDataManager.createIns(upCli=upCli, bnCli=bnCli)
    myGui.setDataManager(dataManager)

    orderManager = await OrderManager.createIns(upCli=upCli, bnCli=bnCli, exInfo=dataManager.getExInfo())

    transferMoney = await TransferMoney.createIns(dataManager, orderManager)
    myGui.setTransferMoney(transferMoney)

    while True:
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())