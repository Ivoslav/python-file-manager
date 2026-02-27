import os
import pytest
import shutil
from datetime import datetime
from utils import format_size, natural_sort_key
from unittest.mock import patch
from operations import (
    copy_single_file, cut_single_file, delete_single_file,
    batch_copy, batch_cut, batch_delete, generate_export_report
)

# ==========================================
# ЧАСТ 1: ТЕСТВАНЕ НА ЛОГИКА И МАТЕМАТИКА
# ==========================================

def test_format_size_small():
    """Тест 1: Проверява дали байтове под 1024 се показват правилно като 'B'"""
    assert format_size(500) == "500.00 B"
    assert format_size(1023) == "1023.00 B"

def test_format_size_large():
    """Тест 2: Проверява преобразуването в MB и GB"""
    assert format_size(1048576) == "1.00 MB"   # Точно 1 Мегабайт
    assert format_size(1572864) == "1.50 MB"   # Мегабайт и половина
    assert format_size(1073741824) == "1.00 GB" # Точно 1 Гигабайт

def test_natural_sort_numbers():
    """Тест 3: Проверява дали 2 застава преди 10 (Естествено сортиране)"""
    files = ["item10.txt", "item2.txt", "item1.txt"]
    sorted_files = sorted(files, key=natural_sort_key)
    assert sorted_files == ["item1.txt", "item2.txt", "item10.txt"]

def test_natural_sort_complex_versions():
    """Тест 4: Проверява сложно сортиране със смесени букви и цифри"""
    files = ["v1.2.10", "v1.2.2", "v1.10.0"]
    sorted_files = sorted(files, key=natural_sort_key)
    assert sorted_files == ["v1.2.2", "v1.2.10", "v1.10.0"]

# ==========================================
# ЧАСТ 2: ТЕСТВАНЕ НА ЕДИНИЧНИ ФАЙЛОВИ ОПЕРАЦИИ
# ==========================================

def test_copy_single_file_success(tmp_path):
    """Тест 5: Успешно копиране на файл"""
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir(); dest_dir.mkdir()
    
    test_file = src_dir / "data.txt"
    test_file.touch()

    result = copy_single_file(str(test_file), str(dest_dir))
    assert result is True
    assert (dest_dir / "data.txt").exists() # Копието съществува
    assert test_file.exists()               # Оригиналът също съществува!

def test_copy_single_file_same_path_protection(tmp_path):
    """Тест 6: ЗАЩИТА! Опит за копиране на файл в същата папка, в която вече е"""
    test_file = tmp_path / "data.txt"
    test_file.touch()

    # Опитваме да го копираме в tmp_path, където вече се намира
    result = copy_single_file(str(test_file), str(tmp_path))
    assert result is False # Функцията трябва да усети измамата и да върне False

def test_cut_single_file_success(tmp_path):
    """Тест 7: Успешно изрязване (Cut) на файл"""
    src_dir = tmp_path / "src"
    dest_dir = tmp_path / "dest"
    src_dir.mkdir(); dest_dir.mkdir()
    
    test_file = src_dir / "move_me.txt"
    test_file.touch()

    result = cut_single_file(str(test_file), str(dest_dir))
    assert result is True
    assert (dest_dir / "move_me.txt").exists() # Файлът е на новото място
    assert not test_file.exists()              # Оригиналът ТРЯБВА да е изтрит!

def test_delete_single_file_not_found(tmp_path):
    """Тест 8: ГРЕШКА! Опит за изтриване на файл, който вече не съществува"""
    fake_file = tmp_path / "ghost.txt"
    
    # pytest.raises проверява дали програмата ни ПРАВИЛНО хвърля грешка
    with pytest.raises(FileNotFoundError):
        delete_single_file(str(fake_file))

# ==========================================
# ЧАСТ 3: ТЕСТВАНЕ НА МАСОВИ ОПЕРАЦИИ (BATCH)
# ==========================================

def test_batch_copy_creates_folders(tmp_path):
    """Тест 9: Проверява дали масовото копиране пресъздава вътрешните папки"""
    base_dir = tmp_path / "base"
    sub_dir = base_dir / "subfolder"
    dest_dir = tmp_path / "dest"
    sub_dir.mkdir(parents=True); dest_dir.mkdir()

    f1 = sub_dir / "deep_file.txt"
    f1.touch()

    # Копираме, като казваме, че base_dir е стартовата точка
    count, err = batch_copy([str(f1)], str(dest_dir), str(base_dir))
    
    assert count == 1
    assert err == 0
    # Дестинацията трябва да е създала /subfolder/deep_file.txt автоматично!
    assert (dest_dir / "subfolder" / "deep_file.txt").exists()

def test_batch_delete_with_mixed_results(tmp_path):
    """Тест 10: Подаваме 1 истински и 1 несъществуващ файл. Трябва да хване грешката."""
    real_file = tmp_path / "real.txt"
    real_file.touch()
    fake_file = str(tmp_path / "fake.txt")

    count, err_count, success_files = batch_delete([str(real_file), fake_file])

    assert count == 1           # Само 1 успешно изтрит
    assert err_count == 1       # Точно 1 засечена грешка
    assert success_files == [str(real_file)]

# ==========================================
# ЧАСТ 4: ТЕСТВАНЕ НА ЕКСПОРТ (РЕПОРТИТЕ)
# ==========================================

def test_generate_export_report_content(tmp_path):
    """Тест 11: Проверява дали генерираният .txt файл има правилен текст вътре"""
    report_path = tmp_path / "report.txt"
    
    # Фалшиви данни: (път, размер, дата, е_системен)
    fake_matched_files = [
        ("C:/fake/user_doc.txt", 1024, datetime(2024, 1, 1, 12, 0), False),
        ("C:/fake/kernel.sys", 500, datetime(2024, 1, 1, 12, 0), True)
    ]
    
    generate_export_report(str(report_path), fake_matched_files, set(), "C:/fake")
    
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    
    assert "ОТЧЕТ ОТ СКАНИРАНЕ (ВСИЧКИ)" in content
    assert "user_doc.txt | Размер: 1.00 KB" in content
    assert "[СИСТЕМЕН] C:/fake/kernel.sys" in content # Системният маркер трябва да е там!

def test_generate_export_report_subset(tmp_path):
    """Тест 12: Експорт само на ИЗБРАНИТЕ (selected) файлове от чекбоксовете"""
    report_path = tmp_path / "report_selected.txt"
    
    fake_matched_files = [
        ("C:/fake/file1.txt", 100, datetime(2024, 1, 1), False),
        ("C:/fake/file2.txt", 200, datetime(2024, 1, 1), False)
    ]
    # Избираме само втория файл!
    selected = {"C:/fake/file2.txt"}
    
    generate_export_report(str(report_path), fake_matched_files, selected, "C:/fake")
    content = report_path.read_text(encoding="utf-8")
    
    assert "ОТЧЕТ ОТ СКАНИРАНЕ (ИЗБРАНИ)" in content
    assert "file2.txt" in content
    assert "file1.txt" not in content # Първият файл не трябва да е в репорта!
    

# --- ТЕСТ 16: КИРИЛИЦА И СПЕЦИАЛНИ СИМВОЛИ ---
def test_unicode_and_special_chars(tmp_path):
    """Тества име на файл, което би объркало лош софтуер"""
    special_name = "Проект_2024_🔥_©.txt"
    src_file = tmp_path / special_name
    src_file.write_text("Съдържание")
    
    dest_dir = tmp_path / "резултати"
    dest_dir.mkdir()
    
    result = copy_single_file(str(src_file), str(dest_dir))
    assert result is True
    assert (dest_dir / special_name).exists()

# --- ТЕСТ 17: СИМУЛАЦИЯ НА ПЪЛЕН ДИСК (Error Handling) ---
def test_copy_failure_disk_full(tmp_path):
    """Симулираме, че дискът е пълен точно по време на копиране"""
    src_file = tmp_path / "large_file.iso"
    src_file.touch()
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    # Използваме 'patch', за да накараме shutil.copy2 да се престори на счупен
    with patch("shutil.copy2", side_effect=OSError("No space left on device")):
        result = copy_single_file(str(src_file), str(dest_dir))
        # Нашата функция трябва да върне False, а не да 'гръмне' цялата програма
        assert result is False

# --- ТЕСТ 18: ОПИТ ЗА ИЗРЯЗВАНЕ ВЪРХУ СЪЩИЯ ФАЙЛ ---
def test_cut_same_path_protection(tmp_path):
    """Проверяваме дали защитата работи и за Cut (Изрязване)"""
    test_file = tmp_path / "important.db"
    test_file.touch()
    
    # Опит да изрежем файл в собствената му папка
    result = cut_single_file(str(test_file), str(tmp_path))
    assert result is False # Трябва да откаже операцията!
    assert test_file.exists() # Файлът не трябва да изчезва при грешка

# --- ТЕСТ 19: СУПЕР ДЪЛЪГ ПЪТ (Linux Path Limit) ---
def test_very_deep_nesting(tmp_path):
    """Тестваме как се справя алгоритъмът със 10 нива на папки"""
    path = tmp_path
    for i in range(10):
        path = path / f"level_{i}"
    path.mkdir(parents=True)
    
    deep_file = path / "deep.txt"
    deep_file.touch()
    
    dest = tmp_path / "backup"
    dest.mkdir()
    
    # Копираме със запазване на структурата
    count, err = batch_copy([str(deep_file)], str(dest), str(tmp_path))
    assert count == 1
    assert err == 0
    
    # ФИКС: Генерираме правилния очакван път с всичките 10 нива
    expected_path = dest
    for i in range(10):
        expected_path = expected_path / f"level_{i}"
    expected_path = expected_path / "deep.txt"
    
    assert expected_path.exists()
    
# --- ТЕСТ 20: ПРАЗНИ СПИСЪЦИ (Edge Case) ---
def test_batch_operations_empty_list():
    """Какво става, ако потребителят натисне 'Копирай', без да е избрал нищо?"""
    # Не трябва да гърми, а просто да връща 0
    count, err = batch_copy([], "/tmp", "/tmp")
    assert count == 0
    assert err == 0
    
    count, err, files = batch_delete([])
    assert count == 0
    assert err == 0
    assert files == []