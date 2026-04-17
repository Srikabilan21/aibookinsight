import os
from pathlib import Path
from dotenv import dotenv_values
import google.generativeai as genai

env_val = dotenv_values(Path('c:/aibookinsight/backend/.env'))
key = env_val.get('GEMINI_API_KEY', '').strip('"\'')
print("Key:", key)

genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-1.5-flash')
res = model.generate_content('say hello')
print("Response:", res.text)
