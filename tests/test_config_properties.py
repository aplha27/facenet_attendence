import os
import pytest
from hypothesis import given, strategies as st
from pathlib import Path
from config.configuration_manager import ConfigurationManager, SystemConfig

# Strategies for generating configuration values
@st.composite
def system_config_strategy(draw):
    return SystemConfig(
        database_url=draw(st.text(min_size=1)),
        upload_directory=Path(draw(st.text(min_size=1))),
        model_directory=Path(draw(st.text(min_size=1))),
        reports_directory=Path(draw(st.text(min_size=1))),
        allowed_file_types=draw(st.lists(st.text(min_size=1, max_size=5), min_size=1)),
        max_file_size=draw(st.integers(min_value=1, max_value=100*1024*1024)),
        face_detection_threshold=draw(st.floats(min_value=0.0, max_value=1.0)),
        recognition_threshold=draw(st.floats(min_value=0.0, max_value=1.0)),
        secret_key=draw(st.text(min_size=5)),
        debug=draw(st.booleans())
    )

def test_default_configuration():
    """Test that default configuration is valid"""
    config_manager = ConfigurationManager(config_file="non_existent.ini")
    config = config_manager.config
    
    assert isinstance(config, SystemConfig)
    assert config.max_file_size > 0
    assert 0.0 <= config.face_detection_threshold <= 1.0
    assert 0.0 <= config.recognition_threshold <= 1.0

@given(st.floats(min_value=0.0, max_value=1.0), 
       st.floats(min_value=0.0, max_value=1.0),
       st.integers(min_value=1))
def test_valid_thresholds_and_size(detection_threshold, recognition_threshold, max_size):
    """Test configuration validation with valid values"""
    # Mock environment variables
    os.environ["FACE_DETECTION_THRESHOLD"] = str(detection_threshold)
    os.environ["RECOGNITION_THRESHOLD"] = str(recognition_threshold)
    os.environ["MAX_FILE_SIZE"] = str(max_size)
    
    config_manager = ConfigurationManager(config_file="non_existent.ini")
    config = config_manager.config
    
    assert config.face_detection_threshold == detection_threshold
    assert config.recognition_threshold == recognition_threshold
    assert config.max_file_size == max_size
    
    # Cleanup
    del os.environ["FACE_DETECTION_THRESHOLD"]
    del os.environ["RECOGNITION_THRESHOLD"]
    del os.environ["MAX_FILE_SIZE"]

@given(st.floats(max_value=-0.0001) | st.floats(min_value=1.0001))
def test_invalid_detection_threshold(threshold):
    """Test that invalid detection thresholds raise ValueError"""
    os.environ["FACE_DETECTION_THRESHOLD"] = str(threshold)
    
    with pytest.raises(ValueError):
        ConfigurationManager(config_file="non_existent.ini")
        
    del os.environ["FACE_DETECTION_THRESHOLD"]

@given(st.floats(max_value=-0.0001) | st.floats(min_value=1.0001))
def test_invalid_recognition_threshold(threshold):
    """Test that invalid recognition thresholds raise ValueError"""
    os.environ["RECOGNITION_THRESHOLD"] = str(threshold)
    
    with pytest.raises(ValueError):
        ConfigurationManager(config_file="non_existent.ini")

    del os.environ["RECOGNITION_THRESHOLD"]

@given(st.integers(max_value=0))
def test_invalid_max_file_size(size):
    """Test that non-positive file sizes raise ValueError"""
    os.environ["MAX_FILE_SIZE"] = str(size)
    
    with pytest.raises(ValueError):
        ConfigurationManager(config_file="non_existent.ini")

    del os.environ["MAX_FILE_SIZE"]

def test_environment_precedence(tmp_path):
    """Test that environment variables take precedence over config file"""
    # Create a temporary config file
    config_file = tmp_path / "test_config.ini"
    config_file.write_text("""
[face_recognition]
detection_threshold = 0.5
""")
    
    # Set environment variable
    os.environ["FACE_DETECTION_THRESHOLD"] = "0.8"
    
    config_manager = ConfigurationManager(config_file=str(config_file))
    
    # Should match environment variable (0.8) not config file (0.5)
    assert config_manager.config.face_detection_threshold == 0.8
    
    del os.environ["FACE_DETECTION_THRESHOLD"]
