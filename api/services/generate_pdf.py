from fpdf import FPDF
from PIL import Image

class PDF(FPDF):
    def add_image_page(self, image_path):
        self.add_page()
        img = Image.open(image_path)
        width, height = img.size
        
        # Pixel --> mm
        mm_width = width * 0.264583
        mm_height = height * 0.264583

        # Escala papel A4        
        max_width, max_height = 190, 270
        aspect = min(max_width / mm_width, max_height / mm_height)
        new_width = mm_width * aspect
        new_height = mm_height * aspect

        # Centralizar        
        x_offset = (210 - new_width) / 2
        y_offset = (297 - new_height) / 2

        self.image(image_path, x_offset, y_offset, new_width, new_height)

def generate(images, output_pdf):
    pdf = PDF()

    for img in images:
        if img[-3:] == 'png':
            if img[:20] == 'resultadosMontecarlo':
                img_path = img
            else: 
                img_path = './resultadosMontecarlo/' + img

            pdf.add_image_page(img_path)
    pdf.output(output_pdf)

