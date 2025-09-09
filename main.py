"""
# Day 2: Printing, Variables, Input --

# Print = make the program talk
print("Hello! I'm Senior AI Buddy (Traning mode)")


# Variables = Little storage boxes
bot_name = "Senior AI Buddy"
version = "v0.0.1"

print(f"My name is {bot_name} and I'm on {version}.")

# Input = ask the user something
user_name = input("What should I call you?")

print(f"Nice to meet you, {user_name}!")

# Tiny decision (logic)
preferred_greeting = input("Do you prefer me to say Nameste or Hello?")

if preferred_greeting.strip().lower() == "nameste":
    print(f"Nameste, {user_name}! I'm here with you.")
else:
    print(f"Hello, {user_name}! I'm here with you.")
    
    # Another practice input
    favorite_drink = input("What's you favorite drink (tea/coffee/water)?")
    print(f"Got it! I'll remember you like {favorite_drink} (for now, only in my head).")
    
    favorite_food = input("What's your favorite food?")
    print(f"Alright {user_name}, I know you like {favorite_drink} and {favorite_food}. Cool!")

    print(" Day 2 complete. Tomorrow I'll get smarter") 
    """
    
# --- Day 3: If/Else and Loops ---

print("Hi, I'm Senior AI Buddy! Type 'quit' anytime to exit.\n")

# Keep chatting until user types 'quit'

while True:
    user_input = input("You: ")
    
    # Check for exit condition
    if user_input.strip().lower() == "quit":
        print("Buddy: Goodbye for now! Stay safe.")
        break
    
    # Simple if/else responses
    elif "hello" in user_input.lower():
        print("Buddy: Hello there! How's you day going?")
    elif "nameste" in user_input.lower():
        print("Buddy: Nameste I'm happy to chat with you.")
    elif "tea" in user_input.lower():
        print("Buddy: Ah, tea is alwaus a good choice.")
    elif "coffee" in user_input.lower():
        print("Buddy: Coffee will keep you energized!")
    else:
        print("Buddy: Hmm, I don't fully understand, but I'm learning!")