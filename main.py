from agents import get_character_description, generate_description, generate_image, evaluate_image, improve_description
from config import MAX_ITERATIONS, TARGET_SCORE

print("=== Dora RL: Cartoon Fusion System ===")

char1_name = input("Enter Character 1: ")
char2_name = input("Enter Character 2: ")

print(f"\nFetching characteristics for {char1_name} from AI...")
char1_desc = get_character_description(char1_name)

print(f"Fetching characteristics for {char2_name} from AI...")
char2_desc = get_character_description(char2_name)

# Step 1: Initial description
print("\nCombining characters...")
description = generate_description(char1_desc, char2_desc)
print("\nCombined Initial Description:\n", description)

best_score = 0
best_image = None

for i in range(1, MAX_ITERATIONS + 1):
    print(f"\n--- Iteration {i} ---")

    # Step 2: Generate image
    image_path = generate_image(description, i)

    # Step 3: Evaluate image
    score, feedback = evaluate_image(image_path, description)

    if score > best_score:
        best_score = score
        best_image = image_path

    # Step 4: Check reward condition
    if score >= TARGET_SCORE:
        print("\nTarget achieved!")
        break

    # Step 5: Improve prompt (Policy Update)
    print("\nImproving prompt based on feedback...")
    description = improve_description(description, feedback)
    print("New Prompt:", description)


print("\n=== Final Result ===")
print("Best Score:", best_score)
print("Best Image:", best_image)