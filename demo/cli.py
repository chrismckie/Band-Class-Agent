import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from main import chat

# Run using python3 demo/cli.py
print("\n┌─────────────────────────────────────┐")
print("│ Welcome to the Band Class Agent CLI │")
print("└─────────────────────────────────────┘\n")

while True:
    print("What would you like to do? Type \"exit\" to quit.")
    user_input = input("> ")
    if user_input == "exit":
        break
    print(chat(user_input))
    print("\n")

print("Good Bye!")