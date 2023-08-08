import os


MSG_HISTORY_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default = 20))


# 管理每個使用者的歷史訊息最多MSG_HISTORY_LIMIT筆1
class HistoryManager:

    def __init__(self):
        self.historyDict = {}
    
    def add_msg(self, userId: str, message: str):
        "根據使用者堆疊紀錄"
        historyMsgOfUser = self.historyDict.get(userId, [])

        if len(historyMsgOfUser) >= MSG_HISTORY_LIMIT:
            historyMsgOfUser.pop(0)

        historyMsgOfUser.append(message)
        self.historyDict[userId] = historyMsgOfUser

    def get_msg(self, userId: str):
        return self.historyDict.get(userId, [])