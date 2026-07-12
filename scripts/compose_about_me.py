from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/SFNSMono.ttf"
FONT_BOLD_PATH = "/System/Library/Fonts/Supplemental/Andale Mono.ttf"

BG = (255, 255, 255)
FG = (36, 41, 46)
ACCENT = (3, 102, 214)
LABEL = (110, 119, 129)

# --- Left: ASCII art, kept as-is (crisp, no recolor) ---
art_src = Image.open("ascii-art.png").convert("RGB")

ART_W = 320
scale = ART_W / art_src.width
art_src = art_src.resize((ART_W, int(art_src.height * scale)), Image.LANCZOS)
ART_H = art_src.height

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
canvas.paste(art_src, (PAD, (canvas_h - ART_H) // 2))

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
