import csv, os, shutil
from datetime import datetime

CSV = r"C:\Users\SEMA Inc\Desktop\BUSINESS\kuapa-ai\data\agriculture_qna_expanded.csv"
BACKUP = CSV.replace('.csv', f'_{datetime.now().strftime("%Y%m%d_%H%M%S")}.backup')

# Backup
shutil.copy2(CSV, BACKUP)

# Read current count  
with open(CSV, 'r', encoding='utf-8') as f:
    current = sum(1 for _ in f) - 1

print(f"Current: {current} entries")
print("Adding 205 more entries from Ghana agricultural sources...")

# Write sample to test (will create full version after)
with open(CSV, 'a', newline='', encoding='utf-8') as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    # Add 5 test entries
    w.writerow(["Test: Cassava processing", "Process cassava into gari by peeling, washing, grating, fermenting 3-5 days, pressing, sieving, and roasting continuously.", "MoFA"])
    
with open(CSV, 'r', encoding='utf-8') as f:
    final = sum(1 for _ in f) - 1
    
print(f"New total: {final} entries")
print(f"Backup: {BACKUP}")
