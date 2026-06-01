import warnings
import os

warnings.filterwarnings("ignore", category=FutureWarning)

from google.api_core import exceptions as google_exceptions
import google.generativeai as genai

# API key
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD9qodXUY1m9VMVOWGmr0p1DFmQ9o5aUuE")
genai.configure(api_key=API_KEY)

# Try these models in order. If your key has no quota for one model,
# the script will try the next model before showing an error.
MODEL_NAMES = [
    "gemini-flash-lite-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

models = [genai.GenerativeModel(model_name) for model_name in MODEL_NAMES]


def ask_gemini(prompt):
    last_error = None

    for model in models:
        try:
            return model.generate_content(prompt)
        except (google_exceptions.NotFound, google_exceptions.ResourceExhausted) as exc:
            last_error = exc
            continue

    raise last_error

print("Gemini AI Started")
print("Type 'exit' to quit\n")

while True:

    try:
        user_input = input("You : ")
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        break

    if user_input.strip().lower() == "exit":
        print("Goodbye!")
        break

    if not user_input.strip():
        continue

    try:
        response = ask_gemini(user_input)
    except google_exceptions.ResourceExhausted:
        print("\nError: Gemini API quota exceeded.")
        print("Your current API key/project has no available free quota for these models.")
        print("Fix: create/use another Gemini API key, enable billing, or wait for quota reset.")
        print("Optional: set a new key with this PowerShell command:")
        print('$env:GEMINI_API_KEY="YOUR_NEW_API_KEY"\n')
        continue
    except Exception as exc:
        print(f"\nError: {exc}")
        print("Please check your internet connection, Gemini API key, quota, and billing.\n")
        continue

    print("\nAI :", response.text)
    print()
