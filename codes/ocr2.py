import cv2
import pytesseract
import os
from dotenv import load_dotenv
import json
import csv
from collections import defaultdict
from groq import Groq  # Groq client import

# Load environment variables
load_dotenv()

# Initialize GROQ client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def process_receipt(image_path, client):
    try:
        # Read and process image
        image = cv2.imread(image_path, 0)
        if image is None:
            raise FileNotFoundError(f"Image not loaded: {image_path}")

        # Perform OCR on the image
        text = pytesseract.image_to_string(image)
        print("OCR Output:")
        print(text)

        # Refined prompt
        prompt = f"""
        Extract the list of items purchased, their prices, and categorize each item into a suitable category. Return the result in strict JSON format with the keys 'item', 'price', and 'category' for each entry.

        Receipt Text:
        {text}

        Important:
        - Only return JSON. Do not include any additional explanation or notes.
        """

        # Send the prompt to the LLM
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )

        # Extract the response content
        response_content = chat_completion.choices[0].message.content.strip()

        # Print the LLM response for debugging
        print("\nLLM Response:")
        print(response_content)

        # Strictly parse JSON response
        try:
            categorized_items = json.loads(response_content)
        except json.JSONDecodeError as e:
            print("Failed to parse JSON response from LLM. Error:", e)
            return

        # Write to first CSV (item details)
        output_csv_items = f"{os.path.splitext(image_path)[0]}_receipt_items.csv"
        with open(output_csv_items, 'w', newline='') as csvfile:
            fieldnames = ['Item', 'Price', 'Category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in categorized_items:
                writer.writerow({'Item': item['item'], 'Price': item['price'], 'Category': item['category']})

        print(f"Processed receipt items saved to: {output_csv_items}")

        # Calculate total sum for each category
        category_totals = defaultdict(float)
        for item in categorized_items:
            category_totals[item['category']] += item['price']

        # Write to second CSV (category totals)
        output_csv_totals = f"{os.path.splitext(image_path)[0]}_receipt_totals.csv"
        with open(output_csv_totals, 'w', newline='') as csvfile:
            fieldnames = ['Category', 'Total']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for category, total in category_totals.items():
                writer.writerow({'Category': category, 'Total': total})

        print(f"Processed receipt totals saved to: {output_csv_totals}")

    except Exception as e:
        print(f"An error occurred while processing {image_path}: {e}")


# List of receipt image paths
receipts = [f for f in os.listdir('.') if f.endswith(('.png', '.jpg', '.jpeg'))]

if not receipts:
    print("No receipt images found in the current directory.")
else:
    for receipt in receipts:
        process_receipt(receipt, client)
