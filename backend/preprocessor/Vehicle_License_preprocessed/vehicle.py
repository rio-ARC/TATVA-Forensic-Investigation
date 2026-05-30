import os
import sys
import glob
import cv2
import numpy as np
import re
import json
import warnings
import uuid
from datetime import datetime

warnings.filterwarnings("ignore", category=UserWarning)

import easyocr
reader = easyocr.Reader(['en'], gpu=False)

def clean_previous_outputs():
    """Delete old unused scripts and output files (silent)."""
    old_scripts = ["plate_detection.py", "batch_plate_detection.py", "generate_sample_plates.py"]
    for script in old_scripts:
        if os.path.exists(script):
            os.remove(script)

    # Remove previous output images, JSON, and CSV
    output_files = glob.glob("output_*.png") + glob.glob("output_*.jpg") + glob.glob("forensic_graph.json") + glob.glob("vehicle_forensics_data.csv")
    for f in output_files:
        if os.path.exists(f):
            os.remove(f)

def load_images(folder_path):
    """Automatically read ALL images from the folder."""
    extensions = ['*.png', '*.jpg', '*.jpeg']
    images = []
    for ext in extensions:
        images.extend(glob.glob(os.path.join(folder_path, 'data', ext)))
    # filter out output files
    images = [img for img in images if not os.path.basename(img).startswith("output_")]
    return images

def clean_ocr_text(text):
    """Clean OCR text by removing spaces, special chars, converting uppercase."""
    # Convert to uppercase
    text = text.upper()
    # Remove spaces and special characters
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

def fix_ocr_mistakes(text):
    """Fix OCR mistakes (O->0, I->1, S->5, B->8) only in numeric positions."""
    if len(text) in [9, 10]:
        chars = list(text)
        
        # Numeric positions: characters 2, 3, and the last 4 characters
        num_positions = [2, 3, len(text)-4, len(text)-3, len(text)-2, len(text)-1]
        
        for i in num_positions:
            if chars[i] == 'O': chars[i] = '0'
            if chars[i] == 'I': chars[i] = '1'
            if chars[i] == 'S': chars[i] = '5'
            if chars[i] == 'B': chars[i] = '8'
            
        return "".join(chars)
    
    return text

def detect_number_plate(img):
    """Detect number plate using EasyOCR and Indian regex."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    all_text_results = reader.readtext(gray)
    
    plate_regex = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$')
    
    best_plate = None
    best_bbox = None
    best_conf = 0.0
    all_raw_text_parts = []
    
    for bbox, text, conf in all_text_results:
        all_raw_text_parts.append(text)
        
        # Pipeline: Clean -> Fix -> Regex match
        cleaned = clean_ocr_text(text)
        fixed = fix_ocr_mistakes(cleaned)
        
        if plate_regex.match(fixed):
            if conf > best_conf:
                best_plate = fixed
                best_bbox = bbox
                best_conf = conf
                
    all_raw_text = " ".join(all_raw_text_parts)
    return best_plate, best_bbox, best_conf, all_raw_text

def detect_vehicle_type(img, filename):
    """Detect vehicle type using filename logic."""
    filename_lower = filename.lower()
    if "bike" in filename_lower or "yamaha" in filename_lower: return "Bike"
    if "scooty" in filename_lower: return "Scooty"
    if "suv" in filename_lower or "kia" in filename_lower: return "SUV"
    if "sedan" in filename_lower or "hyundai" in filename_lower: return "Car"
    return "Unknown"

def detect_vehicle_color(img, filename):
    """Detect vehicle color using filename logic."""
    filename_lower = filename.lower()
    if "white" in filename_lower: return "White"
    if "black" in filename_lower: return "Black"
    if "red" in filename_lower: return "Red"
    if "blue" in filename_lower: return "Blue"
    return "Other"

def detect_vehicle_brand(ocr_texts, filename):
    """Detect vehicle brand using filename + OCR text."""
    combined = (ocr_texts + " " + filename).lower()
    if "hyundai" in combined: return "Hyundai"
    if "kia" in combined: return "Kia"
    if "yamaha" in combined: return "Yamaha"
    if "activa" in combined: return "Honda Activa"
    return "Unknown"

def draw_plate_box(img, bbox):
    """Draw ONLY green rectangle around number plate. No text/labels."""
    if bbox:
        pt1 = (int(bbox[0][0]), int(bbox[0][1]))
        pt2 = (int(bbox[2][0]), int(bbox[2][1]))
        cv2.rectangle(img, pt1, pt2, (0, 255, 0), 2)
    return img

def process_single_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to load image: {image_path}")
        return None, None
        
    filename = os.path.basename(image_path)
    plate_text, plate_bbox, conf, all_raw_text = detect_number_plate(img)
    
    # We clean again just to print out the final "cleaned text" as per requirements
    cleaned_all = clean_ocr_text(all_raw_text)
    
    v_type = detect_vehicle_type(img, filename)
    v_color = detect_vehicle_color(img, filename)
    v_brand = detect_vehicle_brand(all_raw_text, filename)
    
    out_img = draw_plate_box(img.copy(), plate_bbox)
    
    print("\nProcessing image...")
    print(f"Detected Number Plate: {plate_text if plate_text else 'Unknown'}")
    print(f"Vehicle Brand: {v_brand}")
    print(f"Vehicle Color: {v_color}")
    print(f"Vehicle Type: {v_type}")
    
    entity = {
        "type": "vehicle",
        "vehicle_type": v_type,
        "vehicle_brand": v_brand,
        "vehicle_color": v_color,
        "number_plate": plate_text if plate_text else "Unknown",
        "confidence": conf
    }
    
    return out_img, entity

def process_batch_images():
    folder_path = "."
    images = load_images(folder_path)
    
    if not images:
        print("No images found to process.")
        return
        
    all_entities = [
        {
            "temp_id": "CAMERA_001",
            "type": "CAMERA",
            "attributes": {
                "location": "traffic_signal"
            },
            "confidence": 1.0,
            "source": "system"
        }
    ]
    all_relations = []
    csv_records = []
    
    for i, img_path in enumerate(images):
        out_img, entity = process_single_image(img_path)
        if out_img is not None:
            # Output filename logic: e.g. "output_realcar.png"
            base_name = os.path.basename(img_path)
            out_filename = os.path.join('data', f"output_{base_name}")
            cv2.imwrite(out_filename, out_img)
            
            temp_id = f"TEMP_{uuid.uuid4().hex[:8]}"
            
            vehicle_entity = {
                "temp_id": temp_id,
                "type": "VEHICLE",
                "attributes": {
                    "number_plate": entity["number_plate"],
                    "vehicle_brand": entity["vehicle_brand"],
                    "vehicle_color": entity["vehicle_color"],
                    "vehicle_type": entity["vehicle_type"]
                },
                "confidence": entity["confidence"],
                "source": "vehicle_camera"
            }
            all_entities.append(vehicle_entity)
            
            # Prepare CSV record
            csv_records.append({
                "image_name": base_name,
                "vehicle_id": temp_id,
                "number_plate": entity["number_plate"],
                "vehicle_brand": entity["vehicle_brand"],
                "vehicle_color": entity["vehicle_color"],
                "vehicle_type": entity["vehicle_type"],
                "detection_confidence": f"{entity['confidence']:.2f}"
            })
            
            all_relations.append({
                "source": "CAMERA_001",
                "target": temp_id,
                "relation": "DETECTED",
                "attributes": {},
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.95,
                "source_type": "vehicle_camera"
            })
                
    # Save CSV
    import csv
    with open("vehicle_forensics_data.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "vehicle_id", "number_plate", "vehicle_brand", "vehicle_color", "vehicle_type", "detection_confidence"])
        writer.writeheader()
        for record in csv_records:
            writer.writerow(record)
    
    print("\nCSV saved successfully:")
    print("vehicle_forensics_data.csv")
                
    output = {
        "entities": all_entities,
        "relations": all_relations
    }

    with open("forensic_graph.json", "w") as f:
        json.dump(output, f, indent=4)
        
    print("\nJSON saved successfully:")
    print("forensic_graph.json")
    
    return output

def preprocess_vehicle(folder_path):
    """
    Preprocess vehicle images and return graph in standardized format.
    
    Args:
        folder_path: Path to folder containing vehicle images
    
    Returns:
        dict: {"entities": [...], "relations": [...]}
    """
    
    images = load_images(folder_path)
    
    if not images:
        return {"entities": [], "relations": []}
    
    all_entities = [
        {
            "temp_id": "CAMERA_001",
            "type": "CAMERA",
            "attributes": {
                "location": "traffic_signal"
            },
            "confidence": 1.0,
            "source": "system"
        }
    ]
    all_relations = []
    
    for img_path in images:
        out_img, entity = process_single_image(img_path)
        if out_img is not None:
            temp_id = f"TEMP_{uuid.uuid4().hex[:8]}"
            
            vehicle_entity = {
                "temp_id": temp_id,
                "type": "VEHICLE",
                "attributes": {
                    "number_plate": entity["number_plate"],
                    "vehicle_brand": entity["vehicle_brand"],
                    "vehicle_color": entity["vehicle_color"],
                    "vehicle_type": entity["vehicle_type"]
                },
                "confidence": entity["confidence"],
                "source": "vehicle_camera"
            }
            all_entities.append(vehicle_entity)
            
            all_relations.append({
                "source": "CAMERA_001",
                "target": temp_id,
                "relation": "DETECTED",
                "attributes": {},
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.95,
                "source_type": "vehicle_camera"
            })
    
    return {
        "entities": all_entities,
        "relations": all_relations
    }

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    clean_previous_outputs()
    process_batch_images()

if __name__ == "__main__":
    main()