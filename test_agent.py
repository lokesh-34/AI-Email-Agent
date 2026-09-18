from agent import run_agent


conversation_history = []


while True:

    user_message = input("\nYou: ")

    if user_message.lower() in [
        "exit",
        "quit"
    ]:
        break

    response, conversation_history = run_agent(
        user_message,
        conversation_history
    )

    print("\nAgent:", response)