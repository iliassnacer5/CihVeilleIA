import os
import google.generativeai as genai

# Configurer la clé
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Choisir le modèle Gemini
model = genai.GenerativeModel("gemini-1.5-pro")

# Exemple de prompt
prompt = """
Tu es un assistant de programmation. Analyse ce code Python et propose des améliorations.
def add_numbers(a, b):
    return a + b
"""

# Générer la réponse
response = model.generate_content(prompt)
print(response.text)
