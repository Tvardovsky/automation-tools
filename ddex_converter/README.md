# 📦 DDEX Packages Converter  

Python automation tool for processing and normalizing **DDEX 3.8.2** delivery packages, including XML structure verification, resource handling, cover art upscaling, and MD5 checksum regeneration.

This tool was originally created for production workflows in digital music distribution—ensuring strict DDEX compliance, automatic XML reconstruction, image normalization, and full package preparation for ingestion by distributors and DSPs.

---

## ✨ Key Features

- 🧩 Parse and modify DDEX XML using `lxml`
- 🧾 Fix XML namespaces, headers, and structural sections (`ReleaseList`, `ResourceList`, etc.)
- 🖼 Automatically upscale cover art to **3000×3000 px** using `Pillow`
- 🔐 Recalculate `MD5` checksums and update XML accordingly
- 📂 Normalize folder structure for resources, metadata, and manifests
- 🧪 Basic validation, error handling, and logging
- 📦 Batch processing for multiple releases inside a package

---

## 📂 Project Structure

```
ddex_converter/
│
├── local_ddex_packages_converter.py   # main conversion script
└── README.md                          # this file
```

---

## 📁 Expected Input Structure

```
INPUT/
└── Batch20240517143820472/
    ├── BatchComplete.txt
    ├── 4065317927880/
    │   ├── some_ddex_file.xml
    │   └── resources/
    │       ├── cover.jpg
    │       ├── 4065317927880_001.flac
    │       └── ...
    └── 1234567890123/
        └── ...
```

The script walks through each release inside the batch, processes the XML, upscales artwork, recalculates MD5, and generates a clean output structure.

---

## 📤 Output Structure (Example)

```
OUTPUT/
└── 17052024_DDEX/
    ├── 4065317927880/
    │   ├── 4065317927880.xml
    │   ├── resources/
    │   │   ├── 4065317927880.jpg
    │   │   ├── 4065317927880_001.flac
    │   │   └── ...
    │   └── ...
    ├── 1234567890123/
    │   └── ...
    └── BatchComplete.txt
```

---

## 🚀 Usage

### 1. Install dependencies

```
pip install lxml Pillow
```

(Add additional dependencies if used in your version.)

---

### 2. Run the converter

```
python3 local_ddex_packages_converter.py
```

The script typically expects predefined folder structure:

- `INPUT/` — input directory  
- `OUTPUT/` — output directory  
- auto-detected batch folders and UPC folders  

Optional CLI example:

```
python3 local_ddex_packages_converter.py --input ./INPUT --output ./OUTPUT
```

---

## 🔍 Processing Workflow

1. Scan `INPUT/` for batch folders  
2. For each batch:
   - Read `BatchComplete.txt` if available  
   - Detect release folders (UPC-based)  
3. For each release:
   - Locate and parse the DDEX XML  
   - Fix namespaces, headers, structural nodes  
   - Verify presence of resources (artwork, audio files)  
   - Resize artwork to **3000×3000** if necessary  
   - Recalculate MD5 for all assets and update XML  
   - Save normalized XML and resources to output folder  
4. Generate a new `BatchComplete.txt`  
5. Log issues, missing files, and skipped releases

---

## 🛠 Tech Stack

- **Python 3**
- `lxml` — XML parsing and manipulation  
- `Pillow` — cover art upscaling  
- `hashlib` — MD5 checksum generation  
- `os`, `shutil`, `pathlib` — file system operations  
- `logging` — optional logging system  

---

## 💡 Practical Use Cases

- Preparing DDEX packages for ingestion by distributors requiring strict schema compliance  
- Normalizing legacy releases to modern standards (e.g., 3000×3000 artwork)  
- Migrating catalogues between DSP/aggregator platforms (KNM → FUGA → custom distributor)  

---

## ⚠️ Notes

This script was built for a real production environment with complex catalog structures.  
Before using in another setup, ensure that:

- folder naming rules match your environment  
- XML structures are compatible  
- additional validation/logging is enabled as needed  

---

## 📄 License  
MIT License
