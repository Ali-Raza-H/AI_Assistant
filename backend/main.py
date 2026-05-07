from llm.llmComs import *

if __name__ == "__main__":    
    while True:
        userInput = input(">>")
        print("")
        streamAnswer(userInput)