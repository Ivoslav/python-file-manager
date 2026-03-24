import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from utils import format_size, natural_sort_key
from operations import (
    scan_directory, copy_single_file, cut_single_file, delete_single_file,
    batch_copy, batch_cut, batch_delete, generate_export_report
)

# ==========================================
# ЧАСТ 1: ТЕСТВАНЕ НА ЛОГИКА И МАТЕМАТИКА (utils.py)
# ==========================================

def test_format_size_small():
    assert format_size(500) == "500.00 B"
    assert format_size(1023) == "1023.00 B"

def test_format_size_large():
    assert format_size(1048576) == "1.00 MB"   
    assert format_size(1572864) == "1.50 MB"   
    assert format_size(1073741824) == "1.00 GB" 

def test_natural_sort_numbers():
    files = ["item10.txt", "item2.txt", "item1.txt"]
    sorted_files = sorted(files, key=natural_sort_key)
    assert sorted_files == ["item1.txt", "item2.txt", "item10.txt"]

def test_natural_sort_complex_versions():
    files = ["v1.2.10", "v1.2.2", "v1.10.0"]
    sorted_files = sorted(files, key=natural_sort_key)
    assert sorted_files == ["v1.2.2", "v1.2.10", "v1.10.0"]

# ==========================================
# ЧАСТ 2: ТЕСТВАНЕ НА СКАНИРАНЕТО (operations.py - scan_directory)
# ==========================================

def test_scan_directory_basic(tmp_path):
    """Проверява дали скенерът намира файлове и правилно засича системните"""
    (tmp_path / "doc.txt").touch()
    (tmp_path / "kernel.sys").touch()
    
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + timedelta(days=1)
    
    root_node, matched, total_size, has_sys = scan_directory(str(tmp_path), start_date, end_date, [])
    
    assert len(matched) == 2
    assert has_sys is True # Трябва да е засякло .sys файла!
    assert "doc.txt" in [f[0] for f in matched]

def test_scan_directory_with_filters(tmp_path):
    """Проверява дали филтърът за разширения работи правилно"""
    (tmp_path / "image.jpg").touch()
    (tmp_path / "script.py").touch()
    (tmp_path / "notes.txt").touch()
    
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + timedelta(days=1)
    
    # Търсим само .jpg и .txt
    _, matched, _, _ = scan_directory(str(tmp_path), start_date, end_date, [".jpg", ".txt"])
    
    assert len(matched) == 2
    found_names = [os.path.basename(f[0]) for f in matched]
    assert "image.jpg" in found_names
    assert "notes.txt" in found_names
    assert "script.py" not in found_names # Python файлът трябва да е игнориран!

# ==========================================
# ЧАСТ 3: ТЕСТВАНЕ НА ЕДИНИЧНИ ФАЙЛОВИ ОПЕРАЦИИ
# ==========================================

def test_copy_single_file_success(tmp_path):
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir(); dest_dir.mkdir()
    
    test_file = src_dir / "data.txt"
    test_file.write_text("Test content")

    result = copy_single_file(str(test_file), str(dest_dir))
    assert result is True
    assert (dest_dir / "data.txt").exists()
    assert test_file.exists()               

def test_copy_single_file_same_path_protection(tmp_path):
    test_file = tmp_path / "data.txt"
    test_file.touch()

    result = copy_single_file(str(test_file), str(tmp_path))
    assert result is False 

def test_cut_single_file_success(tmp_path):
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir(); dest_dir.mkdir()
    
    test_file = src_dir / "move_me.txt"
    test_file.touch()

    result = cut_single_file(str(test_file), str(dest_dir))
    assert result is True
    assert (dest_dir / "move_me.txt").exists() 
    assert not test_file.exists()              

def test_cut_same_path_protection(tmp_path):
    test_file = tmp_path / "important.db"
    test_file.touch()
    
    result = cut_single_file(str(test_file), str(tmp_path))
    assert result is False
    assert test_file.exists()

def test_delete_single_file_success(tmp_path):
    target_file = tmp_path / "delete_me.txt"
    target_file.touch()
    
    result = delete_single_file(str(target_file))
    assert result is True
    assert not target_file.exists()

def test_delete_single_file_not_found(tmp_path):
    fake_file = tmp_path / "ghost.txt"
    result = delete_single_file(str(fake_file))
    assert result is False # Вече връща False (хванато в try-except), а не гърми

# ==========================================
# ЧАСТ 4: ТЕСТВАНЕ НА МАСОВИ ОПЕРАЦИИ (BATCH)
# ==========================================

def test_batch_copy_creates_folders(tmp_path):
    base_dir = tmp_path / "base"
    sub_dir = base_dir / "subfolder"
    dest_dir = tmp_path / "dest"
    sub_dir.mkdir(parents=True); dest_dir.mkdir()

    f1 = sub_dir / "deep_file.txt"
    f1.touch()

    count, err = batch_copy([str(f1)], str(dest_dir), str(base_dir))
    
    assert count == 1
    assert err == 0
    assert (dest_dir / "subfolder" / "deep_file.txt").exists()

def test_batch_cut_success(tmp_path):
    base_dir = tmp_path / "base"
    dest_dir = tmp_path / "dest"
    base_dir.mkdir(); dest_dir.mkdir()
    
    f1 = base_dir / "file1.txt"
    f1.touch()
    
    count, err, success_files = batch_cut([str(f1)], str(dest_dir), str(base_dir))
    assert count == 1
    assert not f1.exists()
    assert (dest_dir / "file1.txt").exists()

def test_batch_delete_success(tmp_path):
    file1 = tmp_path / "f1.txt"
    file2 = tmp_path / "f2.txt"
    file1.touch(); file2.touch()

    count, err_count, success_files = batch_delete([str(file1), str(file2)])

    assert count == 2
    assert err_count == 0
    assert not file1.exists()
    assert not file2.exists()

def test_batch_delete_with_mixed_results(tmp_path):
    real_file = tmp_path / "real.txt"
    real_file.touch()
    fake_file = str(tmp_path / "fake.txt")

    count, err_count, success_files = batch_delete([str(real_file), fake_file])

    assert count == 1           
    assert err_count == 1      
    assert success_files == [str(real_file)]

# ==========================================
# ЧАСТ 5: ТЕСТВАНЕ НА ЕКСПОРТ (РЕПОРТИТЕ)
# ==========================================

def test_generate_export_report_content(tmp_path):
    report_path = tmp_path / "report.txt"
    fake_matched_files = [
        ("C:/fake/user_doc.txt", 1024, datetime(2024, 1, 1, 12, 0), False),
        ("C:/fake/kernel.sys", 500, datetime(2024, 1, 1, 12, 0), True)
    ]
    
    generate_export_report(str(report_path), fake_matched_files, set(), "C:/fake")
    
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "ОТЧЕТ ОТ СКАНИРАНЕ (ВСИЧКИ)" in content
    assert "user_doc.txt | Размер: 1.00 KB" in content
    assert "[СИСТЕМЕН] C:/fake/kernel.sys" in content

def test_generate_export_report_subset(tmp_path):
    report_path = tmp_path / "report_selected.txt"
    fake_matched_files = [
        ("C:/fake/file1.txt", 100, datetime(2024, 1, 1), False),
        ("C:/fake/file2.txt", 200, datetime(2024, 1, 1), False)
    ]
    selected = {"C:/fake/file2.txt"}
    
    generate_export_report(str(report_path), fake_matched_files, selected, "C:/fake")
    content = report_path.read_text(encoding="utf-8")
    assert "ОТЧЕТ ОТ СКАНИРАНЕ (ИЗБРАНИ)" in content
    assert "file2.txt" in content
    assert "file1.txt" not in content

# ==========================================
# ЧАСТ 6: СПЕЦИФИЧНИ СИТУАЦИИ (EDGE CASES)
# ==========================================

def test_unicode_and_special_chars(tmp_path):
    special_name = "Проект_2024_🔥_©.txt"
    src_file = tmp_path / special_name
    src_file.write_text("Съдържание")
    
    dest_dir = tmp_path / "резултати"
    dest_dir.mkdir()
    
    result = copy_single_file(str(src_file), str(dest_dir))
    assert result is True
    assert (dest_dir / special_name).exists()

def test_copy_failure_disk_full(tmp_path):
    src_file = tmp_path / "large_file.iso"
    src_file.touch()
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    with patch("shutil.copy2", side_effect=OSError("No space left on device")):
        result = copy_single_file(str(src_file), str(dest_dir))
        assert result is False

def test_very_deep_nesting(tmp_path):
    path = tmp_path
    for i in range(10): path = path / f"level_{i}"
    path.mkdir(parents=True)
    
    deep_file = path / "deep.txt"
    deep_file.touch()
    
    dest = tmp_path / "backup"
    dest.mkdir()
    
    count, err = batch_copy([str(deep_file)], str(dest), str(tmp_path))
    assert count == 1
    
    expected_path = dest
    for i in range(10): expected_path = expected_path / f"level_{i}"
    expected_path = expected_path / "deep.txt"
    
    assert expected_path.exists()
    
def test_batch_operations_empty_list():
    count, err = batch_copy([], "/tmp", "/tmp")
    assert count == 0
    assert err == 0
    
    count, err, files = batch_delete([])
    assert count == 0
    assert err == 0
    assert files == []