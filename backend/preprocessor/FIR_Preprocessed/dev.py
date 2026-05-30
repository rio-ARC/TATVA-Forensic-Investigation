# ------------Test 1-------------------

# import spacy
# nlp = spacy.load("en_core_web_sm")
# doc = nlp("This is a sentence.")

# for token in doc:
#     print(f"Word: {token.text:10} | POS: {token.pos_:8} | Tag: {token.tag_:6} | Explanation: {spacy.explain(token.pos_)}")


#  ------------Test 2------------------- labels checking of en_core_web_sm model
import spacy

nlp = spacy.load("en_core_web_sm")

# Get all NER labels from the model
labels = nlp.get_pipe('ner').labels
print(f"Total labels: {len(labels)}")
print("Labels:", labels)

import spacy

# Load the model
nlp = spacy.load("en_core_web_sm")

# Get all POS tags from the model
pos_tags = nlp.get_pipe('tagger').labels

print("All POS Tags in spaCy:")
print("pos_tags: ",pos_tags)
# for tag in pos_tags:
#     print(f"{tag}: {spacy.explain(tag)}")



# ------------Test 3-------------------
# import re
# import dateparser
# from datetime import datetime

# def extract_datetime_pairs_regex(text):
#     """
#     Extract date-time pairs using precise regex patterns
#     """
#     # Pattern for "on 5th May 2023 at 3 PM"
#     pattern = r'on\s+(\d+(?:st|nd|rd|th)?\s+\w+\s+\d{4})\s+at\s+(\d+\s*(?:AM|PM|am|pm))'
    
#     # Pattern for "at 11 AM on 6th May 2023"
#     pattern2 = r'at\s+(\d+\s*(?:AM|PM|am|pm))\s+on\s+(\d+(?:st|nd|rd|th)?\s+\w+\s+\d{4})'
    
#     # Pattern for "5th May 2023 at 3 PM" (without 'on')
#     pattern3 = r'(\d+(?:st|nd|rd|th)?\s+\w+\s+\d{4})\s+at\s+(\d+\s*(?:AM|PM|am|pm))'
    
#     pairs = []
    
#     for pattern in [pattern, pattern2, pattern3]:
#         matches = re.finditer(pattern, text, re.IGNORECASE)
#         for match in matches:
#             groups = match.groups()
#             if len(groups) == 2:
#                 if pattern == pattern2:
#                     time_str, date_str = groups
#                 else:
#                     date_str, time_str = groups
                
#                 # Clean and parse
#                 date_str = date_str.strip()
#                 time_str = time_str.strip()
#                 combined = f"{date_str} {time_str}"
                
#                 parsed = dateparser.parse(
#                     combined,
#                     settings={
#                         'PREFER_DATES_FROM': 'past',
#                         'STRICT_PARSING': True,
#                         'DATE_ORDER': 'DMY'
#                     }
#                 )
                
#                 if parsed:
#                     # Verify year matches
#                     year_match = re.search(r'\d{4}', date_str)
#                     if year_match and parsed.year != int(year_match.group()):
#                         continue
                    
#                     pairs.append({
#                         'date': date_str,
#                         'time': time_str,
#                         'datetime': parsed.isoformat()
#                     })
    
#     # Remove duplicates
#     unique = []
#     seen = set()
#     for pair in pairs:
#         key = f"{pair['date']}_{pair['time']}"
#         if key not in seen:
#             seen.add(key)
#             unique.append(pair)
    
#     return unique

# # Test
# text = """The incident occurred on 5th May 2023 at 3 PM and the police arrived on 6th May 2023 at 10 AM.
# Medical help reached at 11 AM on 6th May 2023."""

# results = extract_datetime_pairs_regex(text)

# print("\n" + "="*60)
# print("REGEX-BASED EXTRACTION (MOST RELIABLE)")
# print("="*60)
# for i, r in enumerate(results, 1):
#     print(f"{i}. {r['datetime']} - {r['date']} at {r['time']}")



# Test 3 - debugging fir.py

# import spacy
# import json

# nlp = spacy.load("en_core_web_sm")

# fir_text = """
# Rahul met Arjun near Park Street at 9 PM.
# Later Rahul transferred money to Vikram.
# """

# doc = nlp(fir_text)

# print("="*50)
# print("DEBUG: What SpaCy Detected")
# print("="*50)

# for ent in doc.ents:
#     print(f"Entity: '{ent.text}' → Label: {ent.label_}")

# print("\n" + "="*50)
# print("DEBUG: Sentence Splitting")
# print("="*50)

# for sent in doc.sents:
#     print(f"Sentence: {sent.text[:50]}...")
#     for ent in sent.ents:
#         print(f"  → Entity: '{ent.text}' ({ent.label_})")



