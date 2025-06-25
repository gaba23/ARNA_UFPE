from fpdf import FPDF
from PIL import Image

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.image_count = 0  # garante que todas as imagens apareçam no grid
        

    def add_image_first_page(self, image_paths):
        self.add_page()

        margin = 10
        half_page_height = (297 - 3 * margin - 30) / 2  # 30mm inclui espaço pra logo (20mm) + 10mm de margem
        max_width = 210 - 2 * margin

        for i, image_path in enumerate(image_paths):
            img = Image.open(image_path)
            width, height = img.size
            
            # Pixel --> mm
            mm_width = width * 0.264583
            mm_height = height * 0.264583

            # Escala papel A4
            scale = min(max_width / mm_width, half_page_height / mm_height)
            new_width = mm_width * scale
            new_height = mm_height * scale        

            
            x = (210 - new_width) / 2
            y = margin + i * (half_page_height + margin) + 30  # i = idx, determina se img é a primeira ou segunda

            self.image(image_path, x, y, new_width, new_height)  # adiciona imagem

        self.add_logos()

    def add_image_page(self, image_path):
        if self.image_count % 6 == 0:  # adiciona página se ela não existir e houver imagem não adicionada
            self.add_page()

        # Grade de imagens 2x3
        margin = 10
        grid_cell_width = 180 / 2  
        grid_cell_height = 257 / 3
        position = self.image_count % 6  # quantidade de imagens por página
        row = position // 2
        col = position % 2
        x = margin + col * (grid_cell_width + margin)
        y = margin + row * (grid_cell_height + margin)

        img = Image.open(image_path)
        width, height = img.size
        
        # Pixel --> mm
        mm_width = width * 0.264583
        mm_height = height * 0.264583

        # Escala papel A4        
        scale = min(grid_cell_width / mm_width, grid_cell_height / mm_height)
        new_width = mm_width * scale
        new_height = mm_height * scale

        # Centralizar        
        x_centered = x + (grid_cell_width - new_width) / 2
        y_centered = y + (grid_cell_height - new_height) / 2

        self.image(image_path, x_centered, y_centered, new_width, new_height)  # adiciiona imagem
        self.image_count += 1

        self.add_logos()

    def add_logos(self):  # Adicionar logos
        logo_path_pmd = './static/logoPMD.png'
        logo_path_ufpe = './static/logo-uf.jpeg'
        self.image(logo_path_pmd, x=190 - 20, y=10, w=20)
        self.image(logo_path_ufpe, x=20, y=10, w=10)


def generate(images, output_pdf, param):
    pdf = PDF()

    if param == "mc":  # Monte Carlo
        first_page_img = ['./resultadosMontecarlo/diagrama_atividades.png', './resultadosMontecarlo/grafico_gantt.png']
        pdf.add_image_first_page(first_page_img)  # primeira página (layout especial)

        for img in images:
            if img[-3:] == 'png':  # seleciona somente as imagens da pasta resultados
                if img[:20] == 'resultadosMontecarlo':
                    img_path = img
                else: 
                    img_path = './resultadosMontecarlo/' + img

                if img_path in first_page_img:
                    continue  # primeira página já foi criada
                else:
                    pdf.add_image_page(img_path)

    if param == "pt":  # Pert
        pdf.add_image_page(images)

    pdf.output(output_pdf)

