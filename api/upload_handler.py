import os
import zipfile
import shutil
from pathlib import Path
from typing import Tuple


class UploadHandler:
    def __init__(self, upload_dir: str = "uploads", extract_dir: str = "extracted_tests"):
        self.upload_dir = Path(upload_dir)
        self.extract_dir = Path(extract_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.extract_dir.mkdir(exist_ok=True)

    def save_zip_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded ZIP file"""
        filepath = self.upload_dir / filename
        with open(filepath, "wb") as f:
            f.write(file_content)
        return str(filepath)

    def extract_zip(self, zip_path: str) -> Tuple[bool, str, list]:
        """Extract ZIP and return list of test files"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_path = self.extract_dir / Path(zip_path).stem
                extract_path.mkdir(exist_ok=True)
                zip_ref.extractall(extract_path)

            # Find all test files
            test_files = []
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), extract_path)
                        test_files.append(rel_path)

            return True, str(extract_path), test_files

        except zipfile.BadZipFile:
            return False, "Invalid ZIP file", []
        except Exception as e:
            return False, f"Extract error: {str(e)}", []

    def validate_test_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate test file has proper structure"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            if 'def test_' in content:
                return True, "Valid test file"
            else:
                return False, "No test functions found"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def cleanup_extraction(self, extract_path: str):
        """Clean up extracted files"""
        try:
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path)
            return True
        except Exception:
            return False


upload_handler = UploadHandler()
