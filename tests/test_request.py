"""
Test cases for MinerURequest class
"""
from textbook.mineru import MinerURequest

def test_mineru_request():
    """
    Test the MinerURequest.request() method.
    
    TODO: Replace the placeholder file paths below with actual PDF file paths
    before running this test.
    """
    test_cases = [
        ("tests/images/wiki.png", ["Wikipedia", "Lagrange"]),
    ]
    for test_case in test_cases:
        file,test_contained_strings = test_case
        
        request = MinerURequest(files=[file])
        
        results = request.request()
        
        assert isinstance(results, dict), "Results should be a dictionary"
        
        assert len(results) > 0, "Results dictionary should not be empty"
        
        for test_string in test_contained_strings:
            markdown = list(results.values())[0]["md_content"]
            assert test_string in markdown, f"Results should contain the string {test_string} for file {file}"
