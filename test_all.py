"""
Модул: test_all.py
Описание: Пакет за автоматизирано осигуряване на качеството (Quality Assurance) и 
модулно тестване (Unit Testing). Покрива 100% от критичната бизнес логика, 
включително масови операции, гранични случаи (Edge Cases) и защитния алгоритъм System Shield.
"""
import os
import pytest
import shutil
from datetime import datetime, timedelta
from utils import format_size, natural_sort_key
from unittest.mock import patch
from operations import (
    copy_single_file, cut_single_file, delete_single_file,
    batch_copy, batch_cut, batch_delete, generate_export_report, scan_directory
)

# ==============================================================
# ТЕСТВАНЕ НА ПОМОЩНИ И МАТЕМАТИЧЕСКИ ФУНКЦИИ
# ==============================================================

def test_format_size_small():
    """Верифицира форматирането на байтове при стойности под 1 KB."""
    assert format_size(500) == "500.00 B"
    assert format_size(1023) == "1023.00 B"

def test_format_size_large():
    """Верифицира скалирането на байтове към мегабайти (MB) и гигабайти (GB)."""
    assert format_size(1048576) == "1.00 MB"   
    assert format_size(1572864) == "1.50 MB"   
    assert format_size(1073741824) == "1.00 GB" 

def test_format_size_zero():
    """Граничен тест (Boundary Test) за форматиране на празен файл (0 байта)."""
    assert format_size(0) == "0.00 B"

def test_natural_sort_numbers():
    """Проверява алгоритъма за естествено сортиране (Natural Sorting) при числа в стрингове."""
    files = ["item10.txt", "item2.txt", "item1.txt"]
    sorted_files = sorted(files, key=natural_sort_key)
    assert sorted_files == ["item1.txt", "item2.txt", "item10.txt"]

def test_natural_sort_complex_versions():
    """Проверява лексикографското подреждане при сложни версии на софтуерни пакети."""
    files = ["v1.2.10", "v1.2.2", "v1.10.0"]
    sorted_files = sorted(files, key=natural_sort_key)
    assert sorted_files == ["v1.2.2", "v1.2.10", "v1.10.0"]

# ==============================================================
# ТЕСТВАНЕ НА ЕДИНИЧНИ ФАЙЛОВИ ОПЕРАЦИИ
# ==============================================================

def test_copy_single_file_success(tmp_path):
    """Верифицира успешното копиране на файлов дескриптор между две директории."""
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir(); dest_dir.mkdir()
    
    test_file = src_dir / "data.txt"
    test_file.touch()

    result = copy_single_file(str(test_file), str(dest_dir))
    assert result is True
    assert (dest_dir / "data.txt").exists()
    assert test_file.exists()               

def test_copy_single_file_same_path_protection(tmp_path):
    """Тества механизма за защита от циклично копиране (Same-path protection)."""
    test_file = tmp_path / "data.txt"
    test_file.touch()

    result = copy_single_file(str(test_file), str(tmp_path))
    assert result is False 

def test_cut_single_file_success(tmp_path):
    """Верифицира операцията по преместване (Изрязване) и премахването на оригинала."""
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir(); dest_dir.mkdir()
    
    test_file = src_dir / "move_me.txt"
    test_file.touch()

    result = cut_single_file(str(test_file), str(dest_dir))
    assert result is True
    assert (dest_dir / "move_me.txt").exists() 
    assert not test_file.exists()              

def test_delete_single_file_not_found(tmp_path):
    """Осигурява правилно обработване на грешки (Error Handling) при липсващ файл."""
    fake_file = tmp_path / "ghost.txt"
    result = delete_single_file(str(fake_file))
    assert result is False

def test_cut_same_path_protection(tmp_path):
    """Осигурява защита срещу загуба на данни при преместване в същата директория."""
    test_file = tmp_path / "important.db"
    test_file.touch()
    
    result = cut_single_file(str(test_file), str(tmp_path))
    assert result is False
    assert test_file.exists()

# ==============================================================
# ТЕСТВАНЕ НА МАСОВИ ОПЕРАЦИИ (BATCH PROCESSING)
# ==============================================================

def test_batch_copy_creates_folders(tmp_path):
    """Тества масовото копиране и способността за пресъздаване на относителни пътища."""
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

def test_batch_delete_with_mixed_results(tmp_path):
    """Анализира събирането на статистика при смесени (успешни и неуспешни) операции."""
    real_file = tmp_path / "real.txt"
    real_file.touch()
    fake_file = str(tmp_path / "fake.txt")

    count, err_count, success_files = batch_delete([str(real_file), fake_file])

    assert count == 1           
    assert err_count == 1      
    assert success_files == [str(real_file)]

def test_batch_operations_empty_list():
    """Граничен тест: Подаване на празен масив към функциите за масова обработка."""
    count, err = batch_copy([], "/tmp", "/tmp")
    assert count == 0
    assert err == 0
    
    count, err, files = batch_delete([])
    assert count == 0
    assert err == 0
    assert files == []

# ==============================================================
# ТЕСТВАНЕ НА ГЕНЕРИРАНЕТО НА ОТЧЕТИ И СКАНИРАНЕТО
# ==============================================================

def test_generate_export_report_content(tmp_path):
    """Верифицира структурата и съдържанието на текстовия одитен лог (Audit Log)."""
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
    """Проверява генерирането на репорт само за маркирани (subset) обекти."""
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

def test_scan_directory_empty(tmp_path):
    """Тества поведението на рекурсивния скенер при изолирана и празна среда."""
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + timedelta(days=1)
    
    root_node, matched, total_size, has_sys = scan_directory(str(tmp_path), start_date, end_date, [])
    
    assert len(matched) == 0
    assert total_size == 0
    assert has_sys is False
    
def test_scan_directory_date_out_of_bounds(tmp_path):
    """Верифицира алгоритъма за филтриране по времеви периоди (Timestamps)."""
    old_file = tmp_path / "old_doc.txt"
    old_file.touch()
    
    old_time = (datetime.now() - timedelta(days=5*365)).timestamp()
    os.utime(old_file, (old_time, old_time))
    
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    _, matched, _, _ = scan_directory(str(tmp_path), start_date, end_date, [])
    assert len(matched) == 0
    
def test_system_shield_paths(tmp_path):
    """Проверява архитектурата System Shield за засичане на критични системни пътища."""
    sys_dir = tmp_path / "boot"
    sys_dir.mkdir()
    
    normal_file = sys_dir / "readme.txt"
    normal_file.touch()
    
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + timedelta(days=1)
    
    from utils import SYSTEM_PATHS
    SYSTEM_PATHS.append(str(sys_dir).lower())
    
    _, matched, _, has_sys = scan_directory(str(tmp_path), start_date, end_date, [])
    
    assert has_sys is True
    assert matched[0][3] is True 
    SYSTEM_PATHS.pop()

# ==============================================================
# ТЕСТВАНЕ НА ЕКСТРЕМНИ ГРАНИЧНИ СЛУЧАИ (EDGE CASES)
# ==============================================================

def test_unicode_and_special_chars(tmp_path):
    """Тества съвместимостта на файловата система с Unicode символи и емотикони."""
    special_name = "Проект_2024_🔥_©.txt"
    src_file = tmp_path / special_name
    src_file.write_text("Съдържание")
    
    dest_dir = tmp_path / "резултати"
    dest_dir.mkdir()
    
    result = copy_single_file(str(src_file), str(dest_dir))
    assert result is True
    assert (dest_dir / special_name).exists()

def test_copy_failure_disk_full(tmp_path):
    """Симулира хардуерен отказ (No space left on device) чрез методологията Mocking."""
    src_file = tmp_path / "large_file.iso"
    src_file.touch()
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    with patch("shutil.copy2", side_effect=OSError("No space left on device")):
        result = copy_single_file(str(src_file), str(dest_dir))
        assert result is False

def test_very_deep_nesting(tmp_path):
    """Верифицира поведението на алгоритъма при дълбоко вложени директорийни дървета."""
    path = tmp_path
    for i in range(10):
        path = path / f"level_{i}"
    path.mkdir(parents=True)
    
    deep_file = path / "deep.txt"
    deep_file.touch()
    
    dest = tmp_path / "backup"
    dest.mkdir()
    
    count, err = batch_copy([str(deep_file)], str(dest), str(tmp_path))
    assert count == 1
    assert err == 0
    
    expected_path = dest
    for i in range(10):
        expected_path = expected_path / f"level_{i}"
    expected_path = expected_path / "deep.txt"
    
    assert expected_path.exists()