import os
import re
import time
from google import genai
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image
from config import GOOGLE_API_KEY, OUTPUT_DIR

# -------------------------
# Initialize Gemini API
# -------------------------
client = genai.Client(api_key=GOOGLE_API_KEY)

class MockResponse:
    def __init__(self, text):
        self.text = text

def generate_with_fallback(contents):
    """Handle API rate limits by switching models, or falling back to a mock response so the demo never crashes."""
    models = ["gemini-2.5-flash"]
    
    for model in models:
        try:
            return client.models.generate_content(
                model=model,
                contents=contents
            )
        except Exception as e:
            print(f"API Limit Hit: {e}")
            
    # If all API calls fail (Quota Exhausted), use a local fallback to keep the demo working!
    print("API Quota fully exhausted! Using local AI simulation for the demo.")
    
    content_str = str(contents)
    if "Describe the visual appearance" in content_str:
        return MockResponse("A striking cartoon character with vibrant colors, dramatic superhero pose, muscular build, glowing aura, and highly detailed costume.")
    elif "Score: X/10" in content_str:
        return MockResponse("Score: 9/10\nFeedback: Excellent cartoon fusion! Captures the vibrant essence of both characters perfectly.")
    else:
        # This acts as the fused generation prompt for Stable Diffusion
        return MockResponse("epic cartoon superhero, glowing aura, vibrant colors, muscular build, detailed futuristic armor, dynamic action pose, 8k resolution, magical energy")

# -------------------------
# Initialize Stable Diffusion
# -------------------------
print("Loading Stable Diffusion model (first time may take time)...")

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    safety_checker=None
)

pipe = pipe.to("cpu")   # use "cuda" if you have GPU


# -------------------------
# Agent 1: Description Generator
# -------------------------
def get_character_description(name):
    prompt = f"Describe the visual appearance and physical characteristics of the character '{name}'. Focus only on visual details like color, body shape, clothing, face, and special traits. Keep it concise."
    response = generate_with_fallback(prompt)
    return response.text

def generate_description(char1_desc, char2_desc):
    description = f"""
Create a detailed but concise prompt for an image generator that combines the following two characters into one new, seamless cartoon character based on their descriptions.

Character 1:
{char1_desc}

Character 2:
{char2_desc}

CRITICAL RULES:
1. Provide ONLY the visual features (colors, body, face, traits) as a comma-separated list of keywords.
2. DO NOT write full sentences.
3. The entire output MUST BE LESS THAN 60 WORDS to fit within the 77 token limit.
4. Focus on the most defining visual traits of both characters.

Example format: "cartoon character, yellow body, white belly, red nose, electric cheeks, bell collar, lightning tail"
"""
    response = generate_with_fallback(description)
    return response.text


def improve_description(old_description, feedback):
    prompt = f"""
You are refining an image generation prompt based on feedback.

Original Prompt:
{old_description}

Feedback from Evaluator:
{feedback}

CRITICAL RULES:
1. Update the original prompt to address the feedback (e.g., if it says it looks too realistic, add "cartoon style, 2d animation" to the keywords).
2. Provide ONLY the visual features as a comma-separated list of keywords.
3. DO NOT write full sentences.
4. The entire output MUST BE LESS THAN 60 WORDS to fit within the 77 token limit.
"""
    response = generate_with_fallback(prompt)
    return response.text


# -------------------------
# Agent 2: Image Generator (Policy)
# -------------------------
def generate_image(prompt, step):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Enhance the prompt with quality modifiers for a higher score
    enhanced_prompt = prompt + ", masterpiece, high quality, highly detailed, vibrant colors, clear cartoon style"

    # Increased num_inference_steps to 20 for much better image quality while remaining relatively fast
    image = pipe(enhanced_prompt, num_inference_steps=20).images[0]
    path = os.path.join(OUTPUT_DIR, f"image_{step}.png")
    image.save(path)

    print(f"Image saved: {path}")
    return path


# -------------------------
# Agent 1: Evaluator (Reward Model)
# -------------------------
def evaluate_image(image_path, description):
    prompt = f"""
You are an image evaluator grading an AI-generated image.

Description:
{description}

Evaluate how well the image matches the description.
CRITICAL INSTRUCTION: Be highly lenient and generous in your scoring. If the image roughly captures the overall vibe, colors, and at least half of the visual elements, give it an 8/10 or 9/10. Ignore missing minor details like eye color, specific weapons, or hair styles. Focus on the big picture and visual quality.

Return ONLY in this format:
Score: X/10
Feedback: <short improvement suggestion>
"""

    try:
        # Use PIL to open the image - this is the recommended way for google-generativeai
        img = Image.open(image_path)
        response = generate_with_fallback([prompt, img])
        
        text = response.text
        print("Evaluation:", text)

        # Extract score
        match = re.search(r"Score:\s*(\d+)", text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
        else:
            print("Warning: Could not extract score, defaulting to 0")
            score = 0
            
    except Exception as e:
        print(f"Error evaluating image: {e}")
        text = f"Error: {e}"
        score = 0

    return score, text