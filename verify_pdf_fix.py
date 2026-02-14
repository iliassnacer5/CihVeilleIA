
import requests
import time
from reportlab.pdfgen import canvas
import io

# Configuration
API_URL = "http://localhost:8000"
PDF_CONTENT = "This is a test PDF for verification."

def create_test_pdf():
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, PDF_CONTENT)
    p.save()
    buffer.seek(0)
    return buffer

def verify_upload():
    print(f"Creating test PDF with content: '{PDF_CONTENT}'")
    pdf_buffer = create_test_pdf()
    
    files = {
        'file': ('test_verification.pdf', pdf_buffer, 'application/pdf')
    }
    
    print("\n[1/3] Uploading PDF...")
    try:
        response = requests.post(f"{API_URL}/documents/upload", files=files)
        response.raise_for_status()
        result = response.json()
        doc_id = result['id']
        print(f"Success! Document ID: {doc_id}")
    except Exception as e:
        print(f"Upload failed: {e}")
        return False

    print("\n[2/3] Waiting for processing (2s)...")
    time.sleep(2)
    
    print(f"\n[3/3] Retrieving document details for {doc_id}...")
    try:
        response = requests.get(f"{API_URL}/documents/{doc_id}")
        response.raise_for_status()
        doc_details = response.json()
        
        extracted_text = doc_details.get('content', '').strip()
        print(f"Extracted Text: '{extracted_text}'")
        
        if PDF_CONTENT in extracted_text:
            print("\n✅ VERIFICATION PASSED: PDF text was correctly extracted.")
            return True
        else:
            print("\n❌ VERIFICATION FAILED: Extracted text does not match.")
            print(f"Expected to contain: '{PDF_CONTENT}'")
            print(f"Got: '{extracted_text}'")
            return False
            
    except Exception as e:
        print(f"Retrieval failed: {e}")
        return False

if __name__ == "__main__":
    success = verify_upload()
    if not success:
        exit(1)
