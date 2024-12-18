import cv2
import pytesseract
import nltk
import re
import csv
import os
import pandas as pd

# Download necessary NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Define categories and their keywords
categories = {
    'Entertainment': ['restaurant', 'cinema', 'theater', 'food', 'meal'],
    'Investment': ['stock', 'bond', 'finance', 'loan'],
    'Grocery': ['supermarket', 'store', 'market', 'produce'],
    'Shopping': ['retail', 'boutique', 'shop', 'mall'],
    'Transport': ['taxi', 'uber', 'train', 'bus'],
    'HomeUtility': ['electricity', 'water', 'internet', 'gas']
}

def process_receipt(image_path):
    # Read and process image
    image = cv2.imread(image_path, 0)
    if image is None:
        print(f"Image not loaded: {image_path}")
        return

    text = (pytesseract.image_to_string(image)).lower()
    print(text)

    # Identify date
    match = re.findall(r'\d+[/.-]\d+[/.-]\d+', text)
    st = ' '.join(match)

    # Extract organization name
    sent_tokens = nltk.sent_tokenize(text)
    try:
        head = sent_tokens[0].splitlines()[0]
    except IndexError:
        head = ''

    # Extract prices
    price_pattern = re.compile(r'[\$\£\€](\d+(?:\.\d{1,2})?)')
    prices = price_pattern.findall(text)
    price = list(map(float, prices))
    x = max(price) if price else 0.0  # Total amount

    # Tokenize and filter text
    tokenizer = nltk.RegexpTokenizer(r"\w+")
    new_words = tokenizer.tokenize(text)
    stop_words = set(nltk.corpus.stopwords.words('english'))
    filtered_list = [w for w in new_words if w not in stop_words]

    # Categorize the bill
    category_assigned = False
    for cat, keywords in categories.items():
        if any(word in filtered_list for word in keywords):
            category = cat
            category_assigned = True
            break
    if not category_assigned:
        category = 'Others'

    filename = f'{category.lower()}.csv'

    # Append row to CSV file
    row_contents = [st, head, x]

    def append_list_as_row(file, list_of_elem):
        if not os.path.isfile(file):
            with open(file, 'w', newline='') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow(['Date', 'Organization', 'Amount'])
                spamwriter.writerow(list_of_elem)
        else:
            with open(file, 'a', newline='') as write_obj:
                csv_writer = csv.writer(write_obj)
                csv_writer.writerow(list_of_elem)

    append_list_as_row(filename, row_contents)

# Process each receipt image
receipts = ['r5.png']  # Add paths to your receipt images
for receipt in receipts:
    process_receipt(receipt)

# Data analysis part (run this after all receipts are processed)
# Read and process CSV data
dataframes = {}
for cat in categories.keys():
    filename = f'{cat.lower()}.csv'
    if os.path.isfile(filename):
        df = pd.read_csv(filename)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        dataframes[cat] = df
    else:
        print(f"{filename} not found.")

# Example analysis: print the first few rows of each category
for cat, df in dataframes.items():
    print(f"\n{cat} DataFrame:")
    print(df.head())