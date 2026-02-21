# test_operations.py
import os
from operations import copy_single_file, delete_single_file, batch_delete

def test_copy_single_file(tmp_path):
    # 1. СЪЗДАВАМЕ ТЕСТОВИ ДАННИ (Arrange)
    # Създаваме фалшива папка Източник и файл вътре
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    src_file = src_dir / "test_doc.txt"
    src_file.write_text("Това е тестов файл.")

    # Създаваме фалшива папка Дестинация
    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()

    # 2. ИЗПЪЛНЯВАМЕ НАШАТА ФУНКЦИЯ (Act)
    result = copy_single_file(str(src_file), str(dest_dir))

    # 3. ПРОВЕРЯВАМЕ РЕЗУЛТАТИТЕ (Assert)
    assert result is True # Функцията трябва да е върнала True
    assert (dest_dir / "test_doc.txt").exists() # Файлът трябва да се е появил в Дестинацията
    assert src_file.exists() # Оригиналът трябва още да си стои в Източника (защото е копиране, а не изрязване)

def test_delete_single_file(tmp_path):
    # 1. Arrange
    target_file = tmp_path / "delete_me.txt"
    target_file.write_text("Сбогом свят")
    assert target_file.exists() # Уверяваме се, че наистина е създаден

    # 2. Act
    result = delete_single_file(str(target_file))

    # 3. Assert
    assert result is True
    assert not target_file.exists() # Файлът ВЕЧЕ НЕ ТРЯБВА да съществува

def test_batch_delete(tmp_path):
    # Създаваме 3 фалшиви файла
    file1 = tmp_path / "f1.txt"
    file2 = tmp_path / "f2.txt"
    file3 = tmp_path / "f3.txt"
    file1.touch()
    file2.touch()
    file3.touch()

    files_to_delete = [str(file1), str(file2), str(file3)]

    # Изпълняваме масовото триене
    count, err_count, success_files = batch_delete(files_to_delete)

    # Проверяваме дали е изтрило точно 3 файла без грешки
    assert count == 3
    assert err_count == 0
    assert len(success_files) == 3
    assert not file1.exists()
    assert not file2.exists()