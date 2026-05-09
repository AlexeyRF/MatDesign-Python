import os
import platform
import subprocess
import ctypes
import math
from colorthief import ColorThief
from PIL import Image

def _get_windows_wallpaper():
    """Скрытая функция для получения обоев в Windows."""
    SPI_GETDESKWALLPAPER = 0x0073
    path_buffer = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 512, path_buffer, 0)
    return path_buffer.value

def _get_linux_wallpaper():
    """Скрытая функция для получения обоев в Linux (GNOME)."""
    try:
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'],
            capture_output=True, text=True, check=True
        )
        path = result.stdout.strip().strip("'").strip('"')
        if path.startswith('file://'):
            path = path[7:]
        return path
    except Exception:
        return None

def get_wallpaper_path():
    """Определяет ОС и возвращает путь к текущим обоям."""
    system = platform.system()
    if system == 'Windows':
        return _get_windows_wallpaper()
    elif system == 'Linux':
        return _get_linux_wallpaper()
    return None

def color_distance(c1, c2):
    """
    Вычисляет евклидово расстояние между двумя RGB цветами в 3D пространстве.
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def get_materials(color_count):
    """
    Возвращает список цветов обоев.
    Цвета отсортированы от самого светлого до самого тёмного 
    (по расстоянию от черного цвета (0, 0, 0)).
    """
    path = get_wallpaper_path()
    if not path or not os.path.exists(path):
        raise FileNotFoundError("Не удалось найти файл обоев.")
        
    color_thief = ColorThief(path)
    palette = color_thief.get_palette(color_count=color_count, quality=1)
    
    # Сортируем: чем больше расстояние от (0, 0, 0), тем цвет светлее.
    # reverse=True означает сортировку по убыванию (сначала самые светлые)
    palette.sort(key=lambda color: color_distance(color, (0, 0, 0)), reverse=True)
    
    return palette

def get_safe_materials(color_count, min_distance):
    """
    Проверяет расстояние между самым светлым и самым тёмным цветами.
    Если оно меньше min_distance, возвращает False. Иначе - список цветов.
    """
    colors = get_materials(color_count)
    if not colors:
        return False
        
    lightest = colors[0]
    darkest = colors[-1]
    
    # Расстояние между "концами" (самым светлым и самым темным)
    distance = color_distance(lightest, darkest)
    
    if distance < min_distance:
        return False
        
    return colors

def is_available(min_distance):
    """
    Собирает все цвета с фото и возвращает количество цветов, 
    которые находятся на расстоянии >= min_distance друг от друга.
    Если таких цветов меньше 2, возвращает 0.
    """
    path = get_wallpaper_path()
    if not path or not os.path.exists(path):
        raise FileNotFoundError("Не удалось найти файл обоев.")
        
    # Открываем изображение через Pillow
    img = Image.open(path).convert('RGB')
    
    # Сжимаем картинку для ускорения работы.
    # Иначе перебор миллионов пикселей 4K обоев займет много времени, 
    # а на пропорции и наличие цветов сжатие практически не повлияет.
    img.thumbnail((250, 250)) 
    
    # Получаем все уникальные пиксели (цвета) изображения
    unique_colors = list(set(img.getdata()))
    
    valid_colors = []
    
    for color in unique_colors:
        # Проверяем, находится ли текущий цвет на достаточном расстоянии 
        # от всех уже добавленных в список valid_colors
        if all(color_distance(color, v) >= min_distance for v in valid_colors):
            valid_colors.append(color)
            
    count = len(valid_colors)
    
    # Если подходящих пар нет (всего 0 или 1 цвет), по условию возвращаем 0
    return count if count >= 2 else 0

# --- Пример использования модуля ---
"""
if __name__ == "__main__":
    print("=== Тестирование модуля ===")
    
    try:
        print("\n1. get_materials(5):")
        colors = get_materials(5)
        for i, c in enumerate(colors):
            dist_to_black = round(color_distance(c, (0,0,0)), 2)
            print(f"  {i+1}. RGB: {c} (Светлота/Расстояние от черного: {dist_to_black})")
            
        print("\n2. get_safe_materials(5, 100):")
        safe_colors = get_safe_materials(5, 100)
        if safe_colors:
            print(f"  Успешно! Расстояние достаточное. Цвета: {safe_colors}")
        else:
            print("  False (Разница между самым светлым и самым темным меньше 100)")
            
        print("\n3. is_available(100):")
        available_count = is_available(100)
        print(f"  Количество уникальных контрастных цветов на фото: {available_count}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
"""