from PIL import Image

# Abres tu imagen en escala de grises
img = Image.open("template/logoGris.jpg").convert("L")

# Color verde institucional
verde = (45, 122, 62)

# Convertir a RGB aplicando el verde proporcionalmente
img_verde = Image.merge("RGB", (
    img.point(lambda p: p * (verde[0]/255)),
    img.point(lambda p: p * (verde[1]/255)),
    img.point(lambda p: p * (verde[2]/255))
))

img_verde.save("voucher_verde.png")