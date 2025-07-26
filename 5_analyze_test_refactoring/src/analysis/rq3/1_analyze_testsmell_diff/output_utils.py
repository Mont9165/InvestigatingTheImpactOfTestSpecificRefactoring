import os
import logging

logger = logging.getLogger(__name__)

def ensure_output_directory(output_dir):
    """出力ディレクトリが存在することを確認し、必要に応じて作成する"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
    return output_dir

def get_output_path(output_dir, filename):
    """出力ファイルの完全パスを取得する"""
    ensure_output_directory(output_dir)
    return os.path.join(output_dir, filename)
