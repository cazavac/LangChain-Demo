
import os
import dotenv
from langsmith import Client

dotenv.load_dotenv()

#print("DATASET_ID:", os.getenv("DATASET_ID"))
#print("LANGSMITH_API_KEY:", os.getenv("LANGSMITH_API_KEY"))

"""## Example Inputs and Outputs

This section defines a list of example input prompts and expected AI responses to test the Book Nook AI's functionality, including literary knowledge and store-related queries.
"""

# --- Book Nook ---
# This set includes more direct, factual questions about books and authors
# to test the AI's literary knowledge, alongside other key functions.

example_inputs = [
    (
        "Who wrote the Sherlock Holmes stories?",
        "The brilliant Sherlock Holmes stories were written by **Sir Arthur Conan Doyle**. Are you thinking of diving into his classic mysteries?",
    ),
    (
        "Who wrote Dracula?",
        "**Bram Stoker** is the author of the timeless gothic horror novel, 'Dracula'. It's a masterpiece of the genre!",
    ),
    (
        "What is this month's book club pick?",
        "This month, our book club is diving into a classic! We're reading **'Dracula'** by Bram Stoker. We meet on the last Thursday of the month and would love to see you there.",
    ),
    (
        "What are Book Nook's store hours?",
        "Our store hours are:\n\n- **Monday - Saturday:** 10:00 AM to 8:00 PM\n- **Sunday:** 12:00 PM to 6:00 PM\n\nWe look forward to seeing you!",
    ),
    (
        "I need a recommendation. I enjoy classic mysteries like Sherlock Holmes.",
        "That's wonderful taste! If you enjoy the deductive reasoning of Sherlock Holmes, you should definitely try **Agatha Christie's** work, particularly 'And Then There Were None.' It's a masterclass in suspense.",
    ),
    (
        "What is 25 times 8?",
        "My expertise is in the world of books! While I can't help with math, I can certainly help you find a great book on mathematics or logic. Are you interested?",
    ),
]

"""## Uploading Examples to LangSmith

The following cell initializes the LangSmith client, retrieves the dataset ID from the environment, prepares the inputs and outputs, and uploads them to the specified LangSmith dataset.
"""

client = Client()

# Make sure your .env file has the correct LangSmith Dataset ID
dataset_id = os.getenv("DATASET_ID")
if not dataset_id:
    raise ValueError("DATASET_ID not found in .env file. Please set it.")

# Prepare inputs and outputs for bulk creation
inputs = [{"HUMAN": input_prompt} for input_prompt, _ in example_inputs]
outputs = [{"AI": output_answer} for _, output_answer in example_inputs]

print(f"Uploading {len(inputs)} examples to LangSmith Dataset ID: {dataset_id}")

client.create_examples(
    inputs=inputs,
    outputs=outputs,
    dataset_id=dataset_id,
)

print("Examples uploaded successfully!")