from unittest.mock import patch, MagicMock
from src.loopse.core.llm_client import SparkLLMClient

def test_client_init_raises_without_env():
    """缺少环境变量时应抛出ValueError"""
    import os
    with patch.dict(os.environ, {}, clear=True):
        for key in ['XUNFEI_APP_ID', 'XUNFEI_API_KEY', 'XUNFEI_API_SECRET']:
            os.environ.pop(key, None)
