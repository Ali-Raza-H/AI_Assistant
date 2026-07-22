from dotenv import load_dotenv
import os

load_dotenv()


api = os.getenv("CIEL_API")

print(api)