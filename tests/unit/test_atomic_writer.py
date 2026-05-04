from pathlib import Path
from unittest.mock import patch, MagicMock
from src.infrastructure.file_system_utils import AtomicWriter

def test_atomic_writer_success(tmp_path: Path):
    target_file = tmp_path / "test.json"
    content = "{\"key\": \"value\"}"
    
    # Run the atomic write
    AtomicWriter.write(target_file, content)
    
    # Assert
    assert target_file.exists()
    assert target_file.read_text() == content + "\n"

@patch("os.fsync")
def test_atomic_writer_calls_fsync(mock_fsync, tmp_path: Path):
    target_file = tmp_path / "test2.json"
    AtomicWriter.write(target_file, "content")
    
    assert mock_fsync.called

@patch("pathlib.Path.replace")
def test_atomic_writer_cleans_up_on_replace_failure(mock_replace, tmp_path: Path):
    mock_replace.side_effect = Exception("Failed to replace")
    target_file = tmp_path / "test3.json"
    temp_file = target_file.with_suffix(".json.tmp")
    
    try:
        AtomicWriter.write(target_file, "content")
    except Exception as e:
        assert str(e) == "Failed to replace"
        
    assert not temp_file.exists()
    assert not target_file.exists()
