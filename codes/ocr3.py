import cv2
import pytesseract
import re
import csv

# Define categories and their keywords
categories = {
    'Entertainment': ['movie', 'cinema', 'ticket', 'theater', 'food', 'restaurant'],
    'Investment': ['stock', 'bond', 'finance', 'loan'],
    'Grocery': ['supermarket', 'store', 'market', 'produce', 'milk', 'bread'],
    'Shopping': ['retail', 'boutique', 'shop', 'mall', 'clothes', 'apparel'],
    'Transport': ['taxi', 'uber', 'train', 'bus', 'gas', 'fuel'],
    'HomeUtility': ['electricity', 'water', 'internet', 'utility'],
    'Miscellaneous': []
}

# Regex pattern to detect prices
price_pattern = re.compile(r'\d+\.\d{2}')

def parse_receipt_text(text):
    lines = text.split('\n')
    items = []
    
    for line in lines:
        line = line.strip()
        
        # Skip irrelevant lines
        if line.lower().startswith(('manager', 'cashier', 'name', 'qty', 'price', 'sub total', 'cash', 'change', 'thank', 'supermarket', 'tel', 'city index')):
            continue
        
        # Find price in the line
        price_match = price_pattern.search(line)
        if price_match:
            price = price_match.group()
            # Extract item name as the part before the price
            item_name = line[:price_match.start()].strip()
            if item_name:
                # Convert price to float and check if it's greater than 0
                price_value = float(price.replace('$', ''))
                if price_value > 0:
                    items.append({'item': item_name, 'price': price})
    
    return items

def categorize_items(items):
    categorized_items = []
    for item in items:
        item_name = item['item'].lower()
        price = item['price']
        category_assigned = False
        for category, keywords in categories.items():
            if any(keyword in item_name for keyword in keywords):
                categorized_items.append({'item': item['item'], 'price': price, 'category': category})
                category_assigned = True
                break
        if not category_assigned:
            categorized_items.append({'item': item['item'], 'price': price, 'category': 'Miscellaneous'})
    return categorized_items

def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh

def process_receipt(image_path):
    # Read and process image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Image not loaded: {image_path}")
        return

    # Preprocess the image
    processed_image = preprocess_image(image)
    
    text = pytesseract.image_to_string(processed_image)
    print("OCR Output:")
    print(text)

    # Parse receipt to get items
    items = parse_receipt_text(text)
    
    # Categorize each item
    categorized_items = categorize_items(items)
    
    # Write all items to a single CSV file
    with open('receipts.csv', 'a', newline='') as csvfile:
        fieldnames = ['Item', 'Price', 'Category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # Write header if the file is empty
        if csvfile.tell() == 0:
            writer.writeheader()
        for item in categorized_items:
            writer.writerow({'Item': item['item'], 'Price': item['price'], 'Category': item['category']})

# List of receipt image paths
receipts = ['r2.jpg']  # Add paths to your receipt images

# Process each receipt
for receipt in receipts:
    process_receipt(receipt)