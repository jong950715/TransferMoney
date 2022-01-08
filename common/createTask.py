import asyncio
import traceback
import os
import sys

RUNNING_FLAG = [False]


def getRunningFlag():
    return RUNNING_FLAG


def createTask(coro):
    task = asyncio.create_task(coro)
    task.add_done_callback(_handle_task_result)
    return task


def _handle_task_result(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # Task cancellation should not be logged as an error.
    except Exception as e:
        emsg = traceback.format_exc()
        print(emsg)
        RUNNING_FLAG[0] = False
        # os.execl(sys.executable, sys.executable, *sys.argv)
        # raise e
        # exit()
