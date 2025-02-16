from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from flask import Flask, jsonify, request
import os
import requests  # Add this import to handle downloading files from URLs

app = Flask(__name__)

# Register the Thai font
pdfmetrics.registerFont(TTFont('THSarabun', 'THSarabun.ttf'))

def create_watermark(watermark_text, angle=45):
    """
    Create a watermark with specified text and rotation angle.
    """
    # Create a PDF in memory
    packet = BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4  # Dimensions of A4 page

    # Set font and transparency
    c.setFont("THSarabun", 60)  # Set font to THSarabun with size 60
    c.setFillColor(red)  # Set font color to red
    c.setFillAlpha(0.2)  # Set font transparency

    image_path = "http://27.254.173.102:3000/hos.png"
    # Draw the image
    image_width, image_height = 100, 100  # Set image size
    c.drawImage(image_path, width / 2 - image_width / 2, height / 2 - image_height / 2, width=image_width, height=image_height, mask='auto')

    # Translate to the center of the page
    c.translate(width / 2, height / 2)
    
    # Rotate and draw the text
    c.rotate(angle)  # Rotate the text by the given angle
    c.drawCentredString(0, 0, watermark_text)  # Draw text centered at (0, 0)

    # Save the canvas and return the BytesIO object
    c.save()
    packet.seek(0)
    return packet

def add_watermark(input_pdf, output_pdf, watermark_text, angle=45):
    """
    Add a watermark to an input PDF and save the result to an output PDF.
    """
    watermark = create_watermark(watermark_text, angle)
    watermark_pdf = PdfReader(watermark)
    
    input_pdf_reader = PdfReader(input_pdf)
    output_pdf_writer = PdfWriter()
    
    # Ensure the watermark page size matches A4
    watermark_page = watermark_pdf.pages[0]

    for page_num in range(len(input_pdf_reader.pages)):
        page = input_pdf_reader.pages[page_num]
        page_width = float(page.mediabox[2] - page.mediabox[0])
        page_height = float(page.mediabox[3] - page.mediabox[1])

        # Ensure watermark matches the page size
        watermark_page.mediabox = page.mediabox

        # Merge the watermark with the page
        page.merge_page(watermark_page)
        output_pdf_writer.add_page(page)  # Add the page with the watermark to the output file

    # Save the final PDF with watermarks
    with open(output_pdf, "wb") as f:
        output_pdf_writer.write(f)

@app.route('/add-watermark', methods=['POST'])
def watermark_pdf():
    try:
        # รับพารามิเตอร์ JSON จากการร้องขอ
        data = request.get_json()

        input_pdf_path = data['input_pdf']
        output_pdf_path = data['output_pdf']
        watermark_text = data['watermark_text']
        angle = data.get('angle', 45)  # ถ้าไม่กำหนด angle จะใช้ค่า 45 องศาเป็นค่าเริ่มต้น

        # เรียกฟังก์ชัน add_watermark เพื่อลงลายน้ำ
        add_watermark(input_pdf_path, output_pdf_path, watermark_text, angle)
        
        return jsonify({'message': 'Watermark added successfully.'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/merge-pdfs', methods=['POST'])
def merge_pdfs():
    try:

        # return jsonify({'error': f' does not exist'}), 200

        data = request.json

        # return jsonify({'error': f'File {data} does not exist'}), 200


        if not data or 'pdf_files' not in data:
            return jsonify({'error': 'No PDF files provided'}), 400
        
        pdf_files = data['pdf_files']

        # Create a PdfWriter object
        pdf_writer = PdfWriter()

        for pdf_file_info in pdf_files:
            pdf_path = pdf_file_info.get('file_path')
            password = pdf_file_info.get('password')

            # Check if pdf_path is a URL
            if pdf_path.startswith('http://') or pdf_path.startswith('https://'):
                try:
                    # Download the PDF file from the URL
                    response = requests.get(pdf_path)
                    response.raise_for_status()  # Raise an error if the request failed

                    # Save the downloaded file locally
                    pdf_path = 'temp_downloaded_file.pdf'
                    with open(pdf_path, 'wb') as f:
                        f.write(response.content)
                except requests.exceptions.RequestException as e:
                    return jsonify({'error': f'Failed to download file from URL {pdf_path}: {str(e)}'}), 400
            else:
                # Ensure the local file exists
                if not os.path.exists(pdf_path):
                    return jsonify({'error': f'File {pdf_path} does not exist'}), 400

            try:
                # Create a PdfReader object for each file
                pdf_reader = PdfReader(pdf_path)

                # If the PDF is password protected, decrypt it
                if pdf_reader.is_encrypted:
                    if password:
                        pdf_reader.decrypt(password)
                    else:
                        return jsonify({'error': f'File {pdf_path} is password protected, but no password was provided'}), 400

                # Add all pages of the current PDF to the writer object
                for page in range(len(pdf_reader.pages)):
                    pdf_writer.add_page(pdf_reader.pages[page])
            except Exception as e:
                return jsonify({'error': f'Failed to process file {pdf_path}: {str(e)}'}), 400
            
            # Delete the temporary file if it was downloaded from a URL
            if 'temp_downloaded_file.pdf' == pdf_path:
                os.remove(pdf_path)

        # Output merged PDF
        output_file = 'C:\FileImgServer\demo.pdf'

        try:
            with open(output_file, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)
        except Exception as e:
            return jsonify({'error': f'Failed to save merged PDF: {str(e)}'}), 500

        return jsonify({'message': f'Merged PDF saved as {output_file}'}), 200

    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500





if __name__ == '__main__':
    app.run(host='xx.xxx.xx.xx', port=3017)  # ฟังการเชื่อมต่อจากทุก IP บนพอร์ต
