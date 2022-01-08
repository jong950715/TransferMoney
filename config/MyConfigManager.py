from common.SingleTonAsyncInit import SingleTonAsyncInit
from config.config import convertType, _getConfigFromFile, getConfigFromFileFitType, CONFIG_FILE_NAMES
import configparser
from definitions import getRootDir
import json
import asyncio
from collections import deque


class MyConfigManager(SingleTonAsyncInit):
    async def _asyncInit(self):
        self.configs = dict()
        self.loadConfigs()
        self.paramsForPools = deque()

    def loadConfigs(self):
        for configName, fn in CONFIG_FILE_NAMES.items():
            self.configs[configName] = getConfigFromFileFitType(fn)

    def getConfig(self, name):
        return self.configs[name]