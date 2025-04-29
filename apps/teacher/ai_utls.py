
import os
import json
import random
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    print(" DIQQAT: OPENAI_API_KEY topilmadi! AI generatsiyasi ishlamaydi. ")
