from backend.ciel.memory.manager import MemoryManager
from backend.ciel.runtime.logging import log

file = "chatHistoryTools.py"


def loadChatHistory():
    log("debug", f"{file}: load chat history function started")
    chatHistory = MemoryManager().load_chat_history()
    log("info", f"{file}: loaded {len(chatHistory)} chat exchange(s)")
    return chatHistory


def saveChatHistory(userMessage, AIresponse):
    log("debug", f"{file}: save chat history function started")
    MemoryManager().save_chat_exchange(userMessage, AIresponse)
    log("debug", f"{file}: save chat history function finished")


def wipeChatHistory():
    log("debug", f"{file}: wipe chat history function started")
    manager = MemoryManager()
    manager.database.execute("DELETE FROM messages")
    manager.database.execute("DELETE FROM interactions")
    log("debug", f"{file}: wipe chat history function finished")
