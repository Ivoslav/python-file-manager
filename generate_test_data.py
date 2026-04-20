import os
import random
import time
from datetime import datetime, timedelta

# ==========================================
# НАСТРОЙКИ НА ГЕНЕРАТОРА
# ==========================================
TARGET_DIR = "Test_Playground"     # Името на главната папка
NUM_MAIN_FOLDERS = 5               # Брой главни папки
MAX_DEPTH = 3                      # Колко нива навътре да влизат подпапките
FILES_PER_FOLDER = range(0, 15)    # Между 0 и 15 файла във всяка папка (ще генерира и празни папки!)
FILE_SIZES_KB = range(0, 5120)     # Размер на файловете: от 0 KB (празни) до 5 MB
EXTENSIONS = ['.txt', '.pdf', '.docx', '.jpg', '.csv', '.log', '.dll', '.sys']

# Дати: От преди 3 години до днес
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=3 * 365)
start_ts = START_DATE.timestamp()
end_ts = END_DATE.timestamp()

def generate_random_date():
    return start_ts + random.random() * (end_ts - start_ts)

def create_random_file(folder_path):
    ext = random.choice(EXTENSIONS)
    file_name = f"mock_file_{random.randint(1000, 9999)}{ext}"
    full_path = os.path.join(folder_path, file_name)
    size_kb = random.choice(FILE_SIZES_KB)
    try:
        with open(full_path, 'wb') as f:
            if size_kb > 0:
                f.write(os.urandom(size_kb * 1024))
    except Exception as e:
        print(f"Грешка при създаване на файл: {e}")
        return

    random_time = generate_random_date()
    os.utime(full_path, (random_time, random_time))

def build_tree(current_path, current_depth):
    os.makedirs(current_path, exist_ok=True)
    
    num_files = random.choice(FILES_PER_FOLDER)
    for _ in range(num_files):
        create_random_file(current_path)
        
    folder_time = generate_random_date()
    os.utime(current_path, (folder_time, folder_time))
    
    if current_depth < MAX_DEPTH:
        num_subfolders = random.randint(0, 3)
        for i in range(num_subfolders):
            sub_path = os.path.join(current_path, f"Subfolder_{current_depth}_{i}")
            build_tree(sub_path, current_depth + 1)

if __name__ == "__main__":
    print(f"🚀 Започва генериране на тестови данни в папка: {TARGET_DIR}...")
    
    base_path = os.path.abspath(TARGET_DIR)
    os.makedirs(base_path, exist_ok=True)
    
    for i in range(NUM_MAIN_FOLDERS):
        main_folder_path = os.path.join(base_path, f"Project_Folder_{i}")
        build_tree(main_folder_path, 1)
        
    print("✅ Генерирането завърши успешно!")
    print("Сега отвори Smart Manager-а и сканирай тази папка!")