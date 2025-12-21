# This class is used to wrap the request to call the MinerU API
from typing import List, Dict, Any
import requests
import os
FIXED_PARAMS = {
    "output_dir": "./output",
    "lang_list": ["en"],
    "backend": "pipeline",
    "parse_method": "auto",
    "formula_enable": True,
    "table_enable": True,
    "return_md": True,
    "return_middle_json": False,
    "return_model_output": False,
    "return_content_list": False,
    "return_images": False,
    "response_format_zip": False,
    "start_page_id": 0,
    "end_page_id": 99999,
}

API_BASE_URL = os.getenv("MINERU_API_URL", "http://localhost:8000")

class MinerURequest:
    def __init__(self, files: List[str]):
        self.files = files
        self.params = FIXED_PARAMS.copy()

    def set_output_dir(self, output_dir: str):
        self.params["output_dir"] = output_dir

    def set_lang_list(self, lang_list: List[str]):
        self.params["lang_list"] = lang_list

    def set_backend(self, backend: str):
        self.params["backend"] = backend

    def set_parse_method(self, parse_method: str):
        self.params["parse_method"] = parse_method

    def set_formula_enable(self, formula_enable: bool):
        self.params["formula_enable"] = formula_enable

    def set_table_enable(self, table_enable: bool):
        self.params["table_enable"] = table_enable

    def set_return_md(self, return_md: bool):
        self.params["return_md"] = return_md

    def set_return_middle_json(self, return_middle_json: bool):
        self.params["return_middle_json"] = return_middle_json

    def set_return_model_output(self, return_model_output: bool):
        self.params["return_model_output"] = return_model_output

    def set_return_content_list(self, return_content_list: bool):
        self.params["return_content_list"] = return_content_list

    def set_return_images(self, return_images: bool):
        self.params["return_images"] = return_images

    def set_response_format_zip(self, response_format_zip: bool):
        self.params["response_format_zip"] = response_format_zip

    def set_start_page_id(self, start_page_id: int):
        self.params["start_page_id"] = start_page_id

    def set_end_page_id(self, end_page_id: int):
        self.params["end_page_id"] = end_page_id

    def request(self) -> Dict[str, Any]:
        """
        Send the request to the MinerU API and return the results dictionary.
        
        Returns:
            Dict[str, Any]: The JSON response from the API containing the parsing results
        """
        # Construct the full endpoint URL
        endpoint = f"{API_BASE_URL}/file_parse"
        
        # Prepare files for multipart/form-data
        files_to_upload = []
        file_handles = []
        
        try:
            for file_path in self.files:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                # Open file in binary mode and use the filename
                file_obj = open(file_path, 'rb')
                file_handles.append(file_obj)
                files_to_upload.append(('files', (os.path.basename(file_path), file_obj, 'application/pdf')))
            
            # Prepare form data with all parameters
            data = {}
            for key, value in self.params.items():
                # FastAPI handles lists in multipart/form-data by accepting them as-is
                # The requests library will properly format them
                data[key] = value
            
            # Make the POST request
            response = requests.post(
                endpoint,
                files=files_to_upload,
                data=data,
                timeout=300  # 5 minute timeout for large files
            )
            
            # Raise an exception for bad status codes
            response.raise_for_status()
            
            # Return the JSON response as a dictionary
            return response.json().get("results",{})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to send request to MinerU API: {str(e)}")
        finally:
            # Close all file handles
            for file_handle in file_handles:
                try:
                    file_handle.close()
                except Exception:
                    pass  # Ignore errors when closing