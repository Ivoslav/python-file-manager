"""
Модул: generate_test_data.py
Описание: Скрипт за автоматизирано генериране на контролирана тестова среда (Sandbox).
Създава йерархична дървовидна структура от папки и файлове с рандомизирани размери, 
разширения и модифицирани метаданни (времеви маркери) за целите на софтуерното тестване.
"""
import os
import random
import time
from datetime import datetime, timedelta

# ==============================================================
# КОНФИГУРАЦИОННИ ПАРАМЕТРИ НА ГЕНЕРАТОРА
# ==============================================================
TARGET_DIR = "Test_Playground"     # Основна директория за генериране
NUM_MAIN_FOLDERS = 5               # Брой главни директории
MAX_DEPTH = 3                      # Максимална дълбочина на рекурсията за поддиректории
FILES_PER_FOLDER = range(0, 15)    # Диапазон за брой файлове в директория (включва празни папки)
FILE_SIZES_KB = range(0, 5120)     # Диапазон за размер на файловете (от 0 KB до 5 MB)

# Валидни разширения (вкл. системни за тестване на модула System Shield)
EXTENSIONS = ['.txt', '.pdf', '.docx', '.jpg', '.csv', '.log', '.dll', '.sys']

# Дефиниране на времеви прозорец (от 3 години назад до текущия момент)
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=3 * 365)
start_ts = START_DATE.timestamp()
end_ts = END_DATE.timestamp()

def generate_random_date():
    """
    Генерира случаен времеви маркер (Timestamp) в рамките на зададения времеви прозорец.
    
    Връща:
        float: Времеви маркер в секунди.
    """
    return start_ts + random.random() * (end_ts - start_ts)

def create_random_file(folder_path):
    """
    Генерира единичен файл с рандомизирано име, размер, разширение и метаданни.
    
    Параметри:
        folder_path (str): Абсолютен или относителен път до целевата директория.
    """
    ext = random.choice(EXTENSIONS)
    file_name = f"mock_file_{random.randint(1000, 9999)}{ext}"
    full_path = os.path.join(folder_path, file_name)
    
    # Генериране на файлово съдържание със зададения обем от байтове
    size_kb = random.choice(FILE_SIZES_KB)
    try:
        with open(full_path, 'wb') as f:
            if size_kb > 0:
                f.write(os.urandom(size_kb * 1024))
    except Exception as e:
        print(f"Грешка при създаване на файл {full_path}: {e}")
        return

    # Модификация на системните атрибути за дата на създаване и промяна
    random_time = generate_random_date()
    os.utime(full_path, (random_time, random_time))

def build_tree(current_path, current_depth):
    """
    Рекурсивен алгоритъм за изграждане на директорийната йерархия.
    
    Параметри:
        current_path (str): Път до текущата директория.
        current_depth (int): Текущо ниво на вложеност.
    """
    os.makedirs(current_path, exist_ok=True)
    
    # Попълване на текущата директория с рандомизирани файлове
    num_files = random.choice(FILES_PER_FOLDER)
    for _ in range(num_files):
        create_random_file(current_path)
        
    # Модификация на метаданните на самата директория
    folder_time = generate_random_date()
    os.utime(current_path, (folder_time, folder_time))
    
    # Рекурсивно създаване на поддиректории, ако не е достигнат лимитът
    if current_depth < MAX_DEPTH:
        num_subfolders = random.randint(0, 3)
        for i in range(num_subfolders):
            sub_path = os.path.join(current_path, f"Subfolder_{current_depth}_{i}")
            build_tree(sub_path, current_depth + 1)

if __name__ == "__main__":
    print(f"Инициализиране на генериращия процес в директория: {TARGET_DIR}...")
    
    # Създаване на базовата структура
    base_path = os.path.abspath(TARGET_DIR)
    os.makedirs(base_path, exist_ok=True)
    
    # Стартиране на рекурсивното изграждане
    for i in range(NUM_MAIN_FOLDERS):
        main_folder_path = os.path.join(base_path, f"Project_Folder_{i}")
        build_tree(main_folder_path, 1)
        
    print("Процесът по генериране на тестови данни завърши успешно.")