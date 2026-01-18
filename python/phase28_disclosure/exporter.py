import json
import os
from typing import Optional
from .types import PresentationPackage

def export_package(
    package: PresentationPackage, 
    output_path: str, 
    human_initiated: bool = False
) -> str:
    """
    Export the presentation package to disk.
    
    GOVERNANCE:
    - Requires human_initiated=True
    - No network calls
    """
    
    if not human_initiated:
        raise RuntimeError("GOVERNANCE VIOLATION: Human initiation required for export.")
    
    # Ensure directory exists
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    # Write File
    with open(output_path, 'w') as f:
        f.write(package.formatted_content)
        
    return output_path
