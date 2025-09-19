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
    
""""
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
        """
  
'''   
# --- Day 4: Functions in Chatbot ---

print("Hi, I'm Senior AI Buddy! Type 'quite' anytime to exit.\n")

# 1) Define a function for bot responses
def get_response(user_input):
    # Decides how the bot should reply based on user input.
    user_input = user_input.strip().lower()
    
    if user_input == "quite":
        return "quite" # special code to exit
    elif "hello" in user_input:
        return "Hello there! How's your day going?"
    elif "nameste" in user_input:
        return "Nameste! I'm happy to chat with you."
    elif "tea" in user_input:
        return "Ah, tea is always a good choice."
    elif "coffee" in user_input:
        return "Coffee will keep you energized!"
    elif "bye" in user_input:
        return "Bye, my friend. Talk soon!"
    else:
        return "Hmm, I don't fully understand, but I'm learning!"
    
    # 2) Chat loop using the function
while True:
    user_input = input("You: ")
    response = get_response(user_input)
    
    if response == "quite":
        print("Buddy: Goodbye for now! Stay safe.")
        break
    else:
        print("Buddy:", response)
        '''
'''
# --- Day 5: Adding Memory (variables that last while chatting) ---

print("Hi, I'm senior AI Buddy! Type 'quit' anytime to exit.\n")

# Store memory in variables (start empty)
user_name = None
favorite_drink = None

def get_response(user_input):
    # Decides how the bot should reply based on user input.
    global user_name, favorite_drink  # use the memory variables

    user_input = user_input.strip().lower()

    if user_input.startswith("my name is"):
        # Example: "My name is Jiban"
        user_name = user_input.replace("my name is", "").strip().title()
        return f"Nice to meet you, {user_name}! I'll remember your name."

    elif user_input.startswith("i like"):
        # Example: "I like tea"
        favorite_drink = user_input.replace("i like", "").strip()
        return f"Cool! I'll remember you like {favorite_drink}."

    elif "what's my name" in user_input:
        if user_name:
            return f"Your name is {user_name}, of course!"
        else:
            return "Hmm, I don't know your name yet."

    elif "what's my drink" in user_input:
        if favorite_drink:
            return f"You like {favorite_drink}, don’t you? ☕"
        else:
            return "You haven’t told me your favorite drink yet."

    elif user_input == "quit":
        return "quit"

    # Default responses
    if user_name:
        return f"I hear you, {user_name}. I'm learning!"
    else:
        return "I'm learning! Tell me more about yourself."


# --- Main chat loop ---
while True:
    user_input = input("You: ")
    response = get_response(user_input)

    if response == "quit":
        print("Buddy: Goodbye for now! Stay safe.")
        break
    else:
        print("Buddy:", response)

'''

# --- Day 6: Persistent Memory with JSON file ---

from modules.memory import load_profile,save_profile

print("Hi, I'm Senior AI Buddy! Type 'quit' anytime to exit.\n")

# Load memory from file (persist across runs)
profile = load_profile()

def get_response(user_input):
    # Decides how the bot should reply based on user input.
    global profile
    text = user_input.strip()
    
    # Exit
    if text.lower() == "quit":
        return "quit"
    
    # Set name: "My name is Jiban"
    if text.lower().strip().startswith("my name is"):
        name = text[10:].strip().title()
        profile["user_name"] = name
        save_profile(profile)
        return f"Nice to meet you, {name}! I'll remember your name."
    
    # Ask name: "What's my name"
    if "what's my name" in text.lower() or "whats my name" in text.lower():
        if profile["user_name"]:
            return f"Your name is {profile['user_name']}, of course!"
        else:
            return "Hmm, I don't know your name yet."
        
        # Set drink: "I like tea"
    if text.lower().strip().startswith("i like"):
        drink = text[6:].strip().lower()
        profile["favorite_drink"] = drink
        save_profile(profile)
        return f"Cool! I'll remember you like {drink}."
    
    # Ask drink
    if "what's my drink" in text.lower() or "whats my drink" in text.lower():
        if profile.get("favorite_drink"):
            return f"You like {profile['favorite_drink']}, don’t you? ☕" 
        else:
            return "You haven’t told me your favorite drink yet."
        
         # Set food: "I eat momo" OR "My favorite food is momo"
    if text.lower().startswith("i eat"):
        food = text[5:].strip()
        profile["favorite_food"] = food
        save_profile(profile)
        return f"Yum! I'll remember you eat {food}."
    if text.lower().startswith("my favorite food is"):
        food = text[20:].strip()
        profile["favorite_food"] = food
        save_profile(profile)
        return f"Got it! Favorite food: {food}. Saved. 🍽️"
        
        # Ask food
    if "what's my food" in text.lower() or "whats my food" in text.lower():
        if profile.get("favorite_food"):
            return f"Your favorite food is {profile['favorite_food']}."
        else:
            return "You haven't told me your favorite food yet."
        
         # Forget commands
    if text.lower() == "forget my name":
        profile["name"] = None
        save_profile(profile)
        return "Okay, I've forgotten your name."
    if text.lower() == "forget my drink":
        profile["favorite_drink"] = None
        save_profile(profile)
        return "Okay, I've forgotten your favorite drink."
    if text.lower() == "forget my food":
        profile["favorite_food"] = None
        save_profile(profile)
        return "Okay, I've forgotten your favorite food."

    # Default response (personalized if we know your name)
    if profile.get("name"):
        return f"I hear you, {profile['name']}. Tell me more!"
    else:
        return "Hmm, I don't fully understand yet, but I'm learning! 🤓"
    
    # --- Chat loop ---
while True:
    user_input = input("You: ")
    response = get_response(user_input)

    if response == "quit":
        print("Buddy: Goodbye for now! 👋 Stay safe.")
        break
    else:
        print("Buddy:", response)
