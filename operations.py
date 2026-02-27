import os
import shutil
import logging # НОВО
from datetime import datetime
from utils import format_size, SYSTEM_PATHS, SYSTEM_EXTS, TreeNode

# Настройваме логъра да записва в app.log
logging.basicConfig(
    filename='app.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- СКАНИРАНЕ ---
def scan_directory(target_folder, start_date, end_date, valid_exts):
    matched_files = []
    has_system_files = False
    total_size_bytes = 0
    root_node = TreeNode("root")

    # Нормализираме пътя и махаме наклонената черта открая
    target_folder = os.path.normpath(os.path.abspath(target_folder))

    for root, dirs, files in os.walk(target_folder):
        dir_in_range = False
        try:
            dir_mtime = os.path.getmtime(root)
            dir_date = datetime.fromtimestamp(dir_mtime)
            if start_date <= dir_date <= end_date:
                dir_in_range = True
        except (PermissionError, FileNotFoundError): pass

        valid_files_in_dir = []
        for file in files:
            if valid_exts and not any(file.lower().endswith(ext) for ext in valid_exts): continue
            full_path = os.path.normpath(os.path.join(root, file))
            try:
                mtime = os.path.getmtime(full_path)
                file_date = datetime.fromtimestamp(mtime)
                if start_date <= file_date <= end_date:
                    size = os.path.getsize(full_path)
                    abs_path = os.path.abspath(full_path).lower()
                    _, ext = os.path.splitext(file)
                    is_sys = ext.lower() in SYSTEM_EXTS or any(abs_path.startswith(p) for p in SYSTEM_PATHS)
                    if is_sys: has_system_files = True
                    
                    valid_files_in_dir.append((file, full_path, size, file_date, is_sys))
                    matched_files.append((full_path, size, file_date, is_sys))
                    total_size_bytes += size
            except (PermissionError, FileNotFoundError): pass

        if valid_files_in_dir or dir_in_range:
            rel_path = os.path.relpath(root, target_folder)
            current_node = root_node
            if rel_path != '.':
                parts = rel_path.split(os.sep)
                for part in parts:
                    if part not in current_node.children:
                        current_node.children[part] = TreeNode(part)
                    current_node = current_node.children[part]
            current_node.files.extend(valid_files_in_dir)
            
    return root_node, matched_files, total_size_bytes, has_system_files

# --- ЕДИНИЧНИ ОПЕРАЦИИ ---
def copy_single_file(src_path, dest_folder):
    try:
        src_path = os.path.normpath(os.path.abspath(src_path))
        dest_folder = os.path.normpath(os.path.abspath(dest_folder))
        final_dest = os.path.join(dest_folder, os.path.basename(src_path))
        
        if src_path == final_dest:
            return False
            
        shutil.copy2(src_path, final_dest)
        return True
    except Exception:
        return False

def cut_single_file(src_path, dest_folder):
    if copy_single_file(src_path, dest_folder):
        try:
            os.remove(os.path.normpath(os.path.abspath(src_path)))
            return True
        except Exception:
            return False
    return False

def delete_single_file(src_path):
    try:
        os.remove(clean_path(src_path))
        logging.info(f"Успешно изтрит файл: {src_path}") # ЗАПИСВАМЕ В ЛОГА
        return True
    except Exception as e:
        logging.error(f"Грешка при изтриване на {src_path}: {e}") # ЗАПИСВАМЕ ГРЕШКАТА
        return False

# --- МАСОВИ ОПЕРАЦИИ ---
def batch_copy(files_list, dest_folder, target_folder):
    count, err_count = 0, 0
    # КРИТИЧЕН ФИКС: Нормализираме стартовата папка и дестинацията
    target_folder = os.path.normpath(os.path.abspath(target_folder))
    dest_folder = os.path.normpath(os.path.abspath(dest_folder))

    for f_path in files_list:
        try:
            abs_f_path = os.path.normpath(os.path.abspath(f_path))
            # relpath вече ще работи перфектно върху чисти абсолютни пътища
            rel_path = os.path.relpath(abs_f_path, target_folder)
            final_dest = os.path.join(dest_folder, rel_path)
            
            if abs_f_path == os.path.abspath(final_dest): continue
            
            os.makedirs(os.path.dirname(final_dest), exist_ok=True)
            shutil.copy2(abs_f_path, final_dest)
            count += 1
        except Exception:
            err_count += 1
    return count, err_count

def batch_cut(files_list, dest_folder, target_folder):
    count, err_count, success_files = 0, 0, []
    target_folder = os.path.normpath(os.path.abspath(target_folder))
    dest_folder = os.path.normpath(os.path.abspath(dest_folder))
    
    for f_path in files_list:
        try:
            abs_f_path = os.path.normpath(os.path.abspath(f_path))
            rel_path = os.path.relpath(abs_f_path, target_folder)
            final_dest = os.path.join(dest_folder, rel_path)
            
            if abs_f_path == os.path.abspath(final_dest): continue
            
            os.makedirs(os.path.dirname(final_dest), exist_ok=True)
            shutil.copy2(abs_f_path, final_dest)
            os.remove(abs_f_path)
            count += 1
            success_files.append(f_path)
        except Exception: err_count += 1
    return count, err_count, success_files

def batch_delete(files_list):
    count, err_count, success_files = 0, 0, []
    for f_path in files_list:
        try:
            abs_path = os.path.normpath(os.path.abspath(f_path))
            os.remove(abs_path)
            count += 1
            success_files.append(f_path)
        except Exception: err_count += 1
    return count, err_count, success_files

# --- ЕКСПОРТ ---
def generate_export_report(file_path, matched_files, selected_files, target_folder):
    files_to_process = [f for f in matched_files if f[0] in selected_files] if selected_files else matched_files
    is_subset = len(selected_files) > 0
    target_str = "ИЗБРАНИ" if is_subset else "ВСИЧКИ"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"ОТЧЕТ ОТ СКАНИРАНЕ ({target_str}): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Сканирана директория: {target_folder}\n")
        f.write(f"Общо включени файлове: {len(files_to_process)}\n\n")
        for f_path, f_size, f_date, is_sys in files_to_process:
            sys_tag = "[СИСТЕМЕН] " if is_sys else ""
            date_str = f_date.strftime("%d/%m/%Y %H:%M")
            f.write(f"{sys_tag}{f_path} | Размер: {format_size(f_size)} | Дата: {date_str}\n")