import re
import json

def extract_amount_from_line(line: str) -> str:
    """
    Cleans up a text line and extracts the last valid decimal/integer number.
    Handles currency symbols, thousand separators (spaces, commas, dots),
    and decimal punctuation.
    """
    # Remove currency signs and text noise
    cleaned = re.sub(r'[\$€£₽]|[руб|руб\.|rub|rub\.]', '', line, flags=re.IGNORECASE).strip()
    
    # Extract sequences of digits that can include spaces, commas, or dots
    # e.g., "1 234.56", "1,234.56", "1234,56", "1200", "1.234,56"
    matches = re.findall(r'\b\d+(?:[\s,\.]\d+)*\b', cleaned)
    if not matches:
        return ""
    
    # Typically, the amount is the last numeric value on the line
    candidate = matches[-1]
    
    # Strip spaces (thousands separators)
    candidate_clean = re.sub(r'\s+', '', candidate)
    
    # Handle separators
    if '.' in candidate_clean and ',' in candidate_clean:
        # e.g., "1,234.56" -> remove comma
        if candidate_clean.find(',') < candidate_clean.find('.'):
            candidate_clean = candidate_clean.replace(',', '')
        else:
            # e.g., "1.234,56" -> remove dot, replace comma with dot
            candidate_clean = candidate_clean.replace('.', '').replace(',', '.')
    elif ',' in candidate_clean:
        parts = candidate_clean.split(',')
        if len(parts[-1]) == 2:
            # e.g., "1234,56" -> "1234.56"
            candidate_clean = candidate_clean.replace(',', '.')
        else:
            # e.g., "1,234" -> "1234" (thousands separator)
            candidate_clean = candidate_clean.replace(',', '')
    elif '.' in candidate_clean:
        parts = candidate_clean.split('.')
        # If the dot is followed by 3 digits, it's a thousands separator
        if len(parts[-1]) == 3:
            # e.g., "1.234" -> "1234"
            candidate_clean = candidate_clean.replace('.', '')
        # If it's 1 or 2 digits, keep the decimal dot
            
    # Format decimals: ensure "XX.YY"
    if '.' in candidate_clean:
        parts = candidate_clean.split('.')
        if len(parts[-1]) == 1:
            candidate_clean += '0'
        elif len(parts[-1]) > 2:
            # truncate to 2 digits
            candidate_clean = parts[0] + '.' + parts[-1][:2]
    else:
        candidate_clean += '.00'
        
    try:
        # Validate that we ended up with a float
        val = float(candidate_clean)
        return f"{val:.2f}"
    except ValueError:
        return ""

def parse_invoice(text: str) -> dict:
    """
    Parses OCR text and structures it into a dictionary with:
    - Vendor Name
    - Invoice Date
    - Total Amount
    - Items List: [{Quantity, Description, Price}]
    """
    data = {
        "Vendor Name": "Unknown",
        "Invoice Date": "Unknown",
        "Total Amount": "0.00",
        "Items List": []
    }
    
    if not text:
        return data

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # 1. Extract Vendor Name
    # Look at the first 5 lines. Avoid common header terms.
    exclude_keywords = {"invoice", "bill to", "ship to", "date", "total", "amount", "tax", "page", "client", "customer", "инвойс", "счет", "получатель", "плательщик"}
    for line in lines[:5]:
        line_lower = line.lower()
        if len(line) > 2 and not any(kw in line_lower for kw in exclude_keywords):
            data["Vendor Name"] = line
            break

    # 2. Extract Invoice Date
    # Match patterns like: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD.MM.YYYY, Month DD, YYYY
    date_patterns = [
        r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b',
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        r'\b\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'
    ]
    for line in lines:
        for pattern in date_patterns:
            date_match = re.search(pattern, line, re.IGNORECASE)
            if date_match:
                data["Invoice Date"] = date_match.group(0)
                break
        if data["Invoice Date"] != "Unknown":
            break

    # 3. Extract Total Amount
    # Scan lines for total keywords in English and Russian
    total_keywords = {
        'total', 'amount due', 'balance due', 'grand total', 'net total', 
        'sum', 'total to pay', 'to pay', 'итого', 'всего', 'сумма', 'к оплате', 'баланс'
    }
    
    total_found = False
    # First attempt: search bottom-up for total keywords
    for line in reversed(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in total_keywords):
            # Avoid subtotal and tax lines unless we have no other options
            if 'subtotal' in line_lower or 'tax' in line_lower or 'rate' in line_lower or 'налог' in line_lower or 'процент' in line_lower:
                continue
            amt = extract_amount_from_line(line)
            if amt:
                data["Total Amount"] = amt
                total_found = True
                break
                
    # Second attempt: check all lines top-down for total keywords if bottom-up failed
    if not total_found:
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in total_keywords):
                amt = extract_amount_from_line(line)
                if amt:
                    data["Total Amount"] = amt
                    total_found = True
                    break

    # 4. Extract Items Table
    for line in lines:
        line_lower = line.lower()
        # Skip total and header lines
        if any(kw in line_lower for kw in {'total', 'subtotal', 'итого', 'сумма', 'всего', 'invoice', 'date'}):
            continue
            
        # Regex 1: "Quantity Description Price" e.g., "2 x Widget $10.00" or "3 Widget 5.00" or "1 Widget 12.50"
        item_match_1 = re.search(r'^(\d+)\s*x?\s+(.+?)\s+[\$€£₽]?\s*(\d+[.,]\d{1,2})$', line)
        if item_match_1:
            data["Items List"].append({
                "Quantity": item_match_1.group(1),
                "Description": item_match_1.group(2).strip(),
                "Price": item_match_1.group(3).replace(',', '.')
            })
            continue

        # Regex 2: "Description Quantity Price" e.g., "Widget 2 $10.00" or "Widget 2 10.00"
        item_match_2 = re.search(r'^(.+?)\s+(\d+)\s+[\$€£₽]?\s*(\d+[.,]\d{1,2})$', line)
        if item_match_2:
            data["Items List"].append({
                "Quantity": item_match_2.group(2),
                "Description": item_match_2.group(1).strip(),
                "Price": item_match_2.group(3).replace(',', '.')
            })
            continue

        # Regex 3: Simple line containing a description and a price, assuming quantity is 1
        item_match_3 = re.search(r'^([a-zA-Zа-яА-ЯёЁ\s\-]+)\s+[\$€£₽]?\s*(\d+[.,]\d{1,2})$', line)
        if item_match_3:
            data["Items List"].append({
                "Quantity": "1",
                "Description": item_match_3.group(1).strip(),
                "Price": item_match_3.group(2).replace(',', '.')
            })

    return data
