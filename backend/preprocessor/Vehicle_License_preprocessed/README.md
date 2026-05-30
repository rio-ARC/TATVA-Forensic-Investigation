# Vehicle Forensics Preprocessing Module

This module is responsible for preprocessing vehicle forensic data for the Tatva AI Forensics System.

It analyzes vehicle images and extracts:

* Vehicle Number Plate
* Vehicle Brand
* Vehicle Color
* Vehicle Type

The system converts the extracted data into forensic graph entities (nodes) and relations (edges).

---

# Workflow

Vehicle Image
↓
OpenCV Processing
↓
EasyOCR Detection
↓
Vehicle Attribute Extraction
↓
Entity Creation
↓
Relation Mapping
↓
Forensic Graph JSON

---

# Entities (Nodes)

* CAMERA
* VEHICLE

Example:

```json
{
    "temp_id": "TEMP_d6a978f1",
    "type": "VEHICLE",
    "attributes": {
        "number_plate": "TN09BY9726",
        "vehicle_brand": "Hyundai",
        "vehicle_color": "White",
        "vehicle_type": "Car"
    }
}
```

---

# Relations (Edges)

* DETECTED

Example:

```text
CAMERA → DETECTED → VEHICLE
```

---

# Output

The module returns:

```python
{
    "entities": entities,
    "relations": relations
}
```

Generated Files:

* forensic_graph.json
* vehicle_forensics_data.csv
* output_vehicle_detection.png

---

# Technologies Used

* Python
* OpenCV
* EasyOCR
* JSON
* CSV

---

