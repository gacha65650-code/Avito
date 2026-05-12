import os
from PIL import Image, ImageDraw
# перевод из hex в rgb вид для библиотеки
def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))

# отрисовка превью цвета (картинка, которая будет храниться в кэше, чтобы постоянно не вызывать код, чтобы не было нагрузок)
def create_color_preview(hex_string, color_name):
    if not os.path.exists('cache'):
        os.makedirs('cache')
    file_path = f"cache/{color_name.lower()}.png"
    if os.path.exists(file_path):
        return file_path

    hex_list = hex_string.split('-')
    rgb_colors = [hex_to_rgb(c) for c in hex_list]

    size = (150, 150)
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)

    if len(rgb_colors) == 1:
        draw.rectangle([0, 0, size[0], size[1]], fill=rgb_colors[0])
    else:
        for y in range(size[1]):
            section = y / size[1] * (len(rgb_colors) - 1)
            idx = int(section)
            ratio = section - idx
            c1, c2 = rgb_colors[idx], rgb_colors[idx + 1]
            curr_col = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
            draw.line([(0, y), (size[0], y)], fill=curr_col)

    img.save(file_path)
    return file_path