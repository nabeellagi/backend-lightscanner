# LIGHTSCANNER API!
https://backend-lightscanner.fastapicloud.dev/docs

The backend used for the Lightscanner web app!

## Tech Stack Used

1. FastAPI
2. Pillow
3. Numpy
4. Img2PDF

## Why does this exist?

FastAPI offers a simpler approach to create APIs, while Pillow is being used for image processing to apply filters to each given image. While Img2PDF is mainly used for the conversion process, from image files into one single PDF.

## How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/nabeellagi/backend-lightscanner.git
   ```
2. Move into the project directory:
   ```bash
   cd backend-lightscanner
   ```
3. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```
6. Open [http://localhost:8000](http://localhost:8000) to check the API is running.

The API also comes with **auto-generated interactive docs**, available at:
```
http://localhost:8000/docs
```

