import csv

CSV_FILE = r"C:\Users\SEMA Inc\Desktop\BUSINESS\kuapa-ai\data\agriculture_qna_expanded.csv"

# Complete list of 205 new entries covering:
# - Cassava (12), Cocoa (11), Rice (11), Tomato (10), Pepper (7)
# - Okra (5), Yam (9), Plantain (7), Soybean (8), Groundnut (7)
# - Pineapple (7), Orange (7), Oil Palm (8), Irrigation (7)
# - Fertilizers (16), Pests & Diseases (15), Postharvest (13)
# - Water Management (5), Soil Management (9), IPM (8)
# - Value Addition & Marketing (15), Twi translations (5)

# Due to length, adding in batches
entries_batch1 = [
    # Cassava - Ghana's 2nd most important crop
    ("What are the best cassava varieties for Ghana?", "Ampong, Afisiafi, Nkabom, Bankyehemaa, and Dadanyuie are popular high-yielding, disease-resistant varieties. Ampong is very popular for gari and fufu production.", "MoFA / CSIR-PGRRI"),
    ("How do I plant cassava?", "Plant healthy stem cuttings (25-30 cm) at 45° angle, 2/3 buried in mounds or ridges. Use 1m x 1m spacing (10,000 stands/ha). Plant during onset of rains.", "MoFA"),
    ("What is cassava mosaic disease?", "Viral disease causing yellow/white mottling on leaves, stunted growth, and reduced yields. Use resistant varieties like Nkabom; remove and burn infected plants.", "CSIR-CRI"),
    ("How do I control cassava mealybug?", "Introduce natural enemies (parasitoid wasps); maintain field hygiene; avoid planting infected cuttings; apply neem-based insecticides if infestation is severe.", "CSIR-CRI"),
    ("When should I harvest cassava?", "Most varieties mature in 10-12 months; late varieties 18-24 months. Harvest when lower leaves turn yellow. Delay increases root fiber content.", "MoFA"),
]

# Open and append
with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    for q, a, s in entries_batch1:
        w.writerow([q, a, s])

with open(CSV_FILE, 'r', encoding='utf-8') as f:
    total = sum(1 for _ in f) - 1
print(f"Added batch 1. Total now: {total}")
