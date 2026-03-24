import os
from operations import copy_single_file, delete_single_file, batch_delete

def test_copy_single_file(tmp_path):
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    src_file = src_dir / "test_doc.txt"
    src_file.write_text("Това е тестов файл.")

    dest_dir = tmp_path / "destination"
    dest_dir.mkdir()

    result = copy_single_file(str(src_file), str(dest_dir))

    assert result is True 
    assert (dest_dir / "test_doc.txt").exists()
    assert src_file.exists()

def test_delete_single_file(tmp_path):
    target_file = tmp_path / "delete_me.txt"
    target_file.write_text("Сбогом свят")
    assert target_file.exists()

    result = delete_single_file(str(target_file))

    assert result is True
    assert not target_file.exists()

def test_batch_delete(tmp_path):
    file1 = tmp_path / "f1.txt"
    file2 = tmp_path / "f2.txt"
    file3 = tmp_path / "f3.txt"
    file1.touch()
    file2.touch()
    file3.touch()

    files_to_delete = [str(file1), str(file2), str(file3)]

    count, err_count, success_files = batch_delete(files_to_delete)

    assert count == 3
    assert err_count == 0
    assert len(success_files) == 3
    assert not file1.exists()
    assert not file2.exists()