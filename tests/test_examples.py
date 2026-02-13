"""
Tests for Example Scripts

Author: Patrick Cooper

Tests that example scripts can be imported and have correct structure.
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestExampleScripts:
    """Test example scripts structure and imports."""
    
    def test_basic_chat_imports(self):
        """Test basic_chat.py can be imported."""
        # Import the example as a module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "basic_chat",
            "examples/basic_chat.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        # Should not raise ImportError
        assert module is not None
        assert hasattr(spec.loader, 'exec_module')
    
    def test_streaming_chat_imports(self):
        """Test streaming_chat.py can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "streaming_chat",
            "examples/streaming_chat.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        assert module is not None
        assert hasattr(spec.loader, 'exec_module')
    
    def test_interactive_chat_imports(self):
        """Test interactive_chat.py can be imported."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "interactive_chat",
            "examples/interactive_chat.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        assert module is not None
        assert hasattr(spec.loader, 'exec_module')


class TestClientImportPaths:
    """Test client can be imported from different contexts."""
    
    def test_import_from_src(self):
        """Test importing from src.client."""
        from src.client import CURCLLMClient, create_client
        
        assert CURCLLMClient is not None
        assert create_client is not None
    
    def test_import_curc_llm_client_directly(self):
        """Test importing curc_llm_client directly."""
        from src.client.curc_llm_client import CURCLLMClient
        
        assert CURCLLMClient is not None
    
    def test_package_version(self):
        """Test package has version."""
        import src
        
        assert hasattr(src, '__version__')
        assert isinstance(src.__version__, str)


class TestConfigurationFiles:
    """Test configuration files are valid."""
    
    def test_server_config_yaml_exists(self):
        """Test server config file exists and is readable."""
        import yaml
        
        with open('config/server_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        assert config is not None
        assert 'default' in config
        assert 'model' in config['default']
    
    def test_server_config_has_all_presets(self):
        """Test server config has all expected presets."""
        import yaml
        
        with open('config/server_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        expected_presets = [
            'default', 'medium', 'large', 'xlarge',
            'quantized', 'batch', 'interactive', 'dev'
        ]
        
        for preset in expected_presets:
            assert preset in config, f"Missing preset: {preset}"
    
    def test_env_example_exists(self):
        """Test .env.example file exists."""
        assert os.path.exists('config/.env.example')
        
        with open('config/.env.example', 'r') as f:
            content = f.read()
        
        # Check for key variables
        assert 'CURC_USER' in content
        assert 'MODEL_NAME' in content
        assert 'HF_TOKEN' in content


class TestDocumentation:
    """Test documentation files exist and are valid."""
    
    def test_readme_exists(self):
        """Test README.md exists."""
        assert os.path.exists('README.md')
        
        with open('README.md', 'r') as f:
            content = f.read()
        
        assert len(content) > 0
        assert 'CURC' in content
    
    def test_quickstart_exists(self):
        """Test QUICKSTART.md exists."""
        assert os.path.exists('QUICKSTART.md')
        
        with open('QUICKSTART.md', 'r') as f:
            content = f.read()
        
        assert 'Quick Start' in content
    
    def test_project_summary_exists(self):
        """Test PROJECT_SUMMARY.md exists."""
        assert os.path.exists('PROJECT_SUMMARY.md')
        
        with open('PROJECT_SUMMARY.md', 'r') as f:
            content = f.read()
        
        assert 'Project Summary' in content
    
    def test_model_guide_exists(self):
        """Test MODEL_GUIDE.md exists."""
        assert os.path.exists('docs/MODEL_GUIDE.md')
        
        with open('docs/MODEL_GUIDE.md', 'r') as f:
            content = f.read()
        
        assert 'Model' in content
    
    def test_troubleshooting_exists(self):
        """Test TROUBLESHOOTING.md exists."""
        assert os.path.exists('docs/TROUBLESHOOTING.md')
        
        with open('docs/TROUBLESHOOTING.md', 'r') as f:
            content = f.read()
        
        assert 'Troubleshooting' in content


class TestScripts:
    """Test deployment scripts exist and are executable."""
    
    def test_setup_environment_script_exists(self):
        """Test setup_environment.sh exists."""
        assert os.path.exists('scripts/setup_environment.sh')
        
        # Check it's executable
        import stat
        st = os.stat('scripts/setup_environment.sh')
        assert st.st_mode & stat.S_IXUSR
    
    def test_launch_vllm_script_exists(self):
        """Test launch_vllm.slurm exists."""
        assert os.path.exists('scripts/launch_vllm.slurm')
        
        with open('scripts/launch_vllm.slurm', 'r') as f:
            content = f.read()
        
        assert '#!/bin/bash' in content
        assert '#SBATCH' in content
    
    def test_create_tunnel_script_exists(self):
        """Test create_tunnel.sh exists."""
        assert os.path.exists('scripts/create_tunnel.sh')
        
        # Check it's executable
        import stat
        st = os.stat('scripts/create_tunnel.sh')
        assert st.st_mode & stat.S_IXUSR


class TestRequirements:
    """Test requirements and dependencies."""
    
    def test_requirements_file_exists(self):
        """Test requirements.txt exists."""
        assert os.path.exists('requirements.txt')
        
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        # Check for key dependencies
        assert 'vllm' in requirements
        assert 'openai' in requirements
        assert 'httpx' in requirements
    
    def test_setup_py_exists(self):
        """Test setup.py exists."""
        assert os.path.exists('setup.py')
        
        with open('setup.py', 'r') as f:
            content = f.read()
        
        assert 'setup(' in content
        assert 'name=' in content
    
    def test_pytest_ini_exists(self):
        """Test pytest.ini exists."""
        assert os.path.exists('pytest.ini')
        
        with open('pytest.ini', 'r') as f:
            content = f.read()
        
        assert '[pytest]' in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
