from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

bg_image = ImageReader("templateS/KGohne_bg.jpg")

c = canvas.Canvas("final_with_fields.pdf", pagesize=A4)

# Draw the static template background
c.drawImage(bg_image, 0, 0, width=A4[0], height=A4[1])

# Add interactive fields on top
form = c.acroForm

form.textfield(
    name='full_name',
    tooltip='Enter your full name',
    x=500, y=600,
    width=200, height=20,
    borderStyle='inset',
    forceBorder=True,
)
form.checkbox(
    name='confirm',
    tooltip='Confirm',
    x=150, y=550,
    size=15
)

c.drawString(150, 625, "Full Name:")
c.drawString(150, 575, "Confirm:")

c.save()
