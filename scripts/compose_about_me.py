from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/SFNSMono.ttf"
FONT_BOLD_PATH = "/System/Library/Fonts/Supplemental/Andale Mono.ttf"

BG = (13, 17, 23)
FG = (201, 209, 217)
ACCENT = (121, 192, 255)
LABEL = (139, 148, 158)

# --- Left: ASCII art rendered small, dark-on-dark terminal look ---
art_src = Image.open("ascii-art.png").convert("L")

ART_W = 340
scale = ART_W / art_src.width
art_src = art_src.resize((ART_W, int(art_src.height * scale)), Image.LANCZOS)

# gamma curve to punch up midtone density lost when downscaling dense glyphs
art_src = art_src.point(lambda v: int(255 * ((v / 255) ** 1.8)))

# recolor grayscale ASCII into terminal fg-on-bg
art_rgba = Image.new("RGB", art_src.size, BG)
px_gray = art_src.load()
px_out = art_rgba.load()
for y in range(art_src.height):
    for x in range(art_src.width):
        v = px_gray[x, y]
        # darker pixel in source (denser ascii char) -> brighter fg
        t = 1 - (v / 255)
        r = int(BG[0] + (FG[0] - BG[0]) * t)
        g = int(BG[1] + (FG[1] - BG[1]) * t)
        b = int(BG[2] + (FG[2] - BG[2]) * t)
        px_out[x, y] = (r, g, b)

ART_H = art_rgba.height

lines_right = [
    ("akshitharsola@github", "title"),
    ("-" * 22, "rule"),
    ("OS:", "ML Engineer & Robotics"),
    ("Host:", "University of Galway, IE"),
    ("Kernel:", "ROS2 / SLAM / Kalman Filter"),
    ("Uptime:", "3x Published Researcher"),
    ("", ""),
    ("Languages.ML:", "PyTorch, TensorFlow, OpenCV"),
    ("Languages.Prog:", "Python, C++, Kotlin, Swift"),
    ("", ""),
    ("Focus.Robotics:", "GNSS-RTK, LiDAR/IMU/Camera Fusion"),
    ("Focus.Security:", "ML-KEM-768, AES-256-GCM"),
    ("Focus.Agents:", "Multi-agent systems, Local LLMs"),
    ("", ""),
    ("Contact.Email:", "harsolaakshit@gmail.com"),
    ("Contact.LinkedIn:", "akshit-harsola"),
    ("Contact.ORCID:", "0009-0002-6243-5192"),
    ("Contact.GitHub:", "akshitharsola"),
]

font_size = 15
font = ImageFont.truetype(FONT_PATH, font_size)
font_bold = ImageFont.truetype(FONT_BOLD_PATH, font_size)
line_h = int(font_size * 1.55)

PAD = 28
GAP = 34
label_w = max(font_bold.getlength(l) for l, _ in lines_right if l)
value_w = max(font.getlength(v) for _, v in lines_right if v)
RIGHT_W = int(label_w + 14 + value_w)
canvas_h = max(ART_H, line_h * len(lines_right)) + PAD * 2
canvas_w = PAD + ART_W + GAP + RIGHT_W + PAD

canvas = Image.new("RGB", (int(canvas_w), int(canvas_h)), BG)
canvas.paste(art_rgba, (PAD, (canvas_h - ART_H) // 2))

draw = ImageDraw.Draw(canvas)
x0 = PAD + ART_W + GAP
y = PAD + (canvas_h - PAD * 2 - line_h * len(lines_right)) // 2

for label, value in lines_right:
    if not label:
        y += line_h
        continue
    if label == "akshitharsola@github":
        draw.text((x0, y), label, font=font_bold, fill=ACCENT)
    elif label.startswith("-"):
        draw.text((x0, y), label, font=font, fill=LABEL)
    else:
        draw.text((x0, y), label, font=font_bold, fill=ACCENT)
        draw.text((x0 + label_w + 14, y), value, font=font, fill=FG)
    y += line_h

canvas.save("about-me.png")
print("saved", canvas.size)
