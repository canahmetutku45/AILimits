"""Uygulama ikonunu (icon.ico) uretir: koyu zemin uzerinde dolu halka gosterge."""
from PIL import Image, ImageDraw

S = 256
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((8, 8, S - 8, S - 8), radius=56, fill=(32, 34, 40, 255))
box = (44, 44, S - 44, S - 44)
w = 30
d.arc(box, 0, 360, fill=(58, 61, 68, 255), width=w)            # iz
d.arc(box, -90, -90 + 0.66 * 360, fill=(63, 180, 122, 255), width=w)   # yesil dolu kisim
d.arc(box, -90 + 0.66 * 360, -90 + 0.82 * 360, fill=(224, 164, 58, 255), width=w)  # sari
# ortada uc kucuk cubuk (farkli limitler)
for i, (h, col) in enumerate([(46, (63, 180, 122)), (70, (63, 180, 122)), (30, (224, 164, 58))]):
    x = 100 + i * 22
    d.rounded_rectangle((x, 160 - h, x + 14, 160), radius=5, fill=col + (255,))
im.save("icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
im.save("icon.png")
print("icon.ico hazir")
