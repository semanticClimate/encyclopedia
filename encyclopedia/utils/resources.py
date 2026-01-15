"""
Resource paths and configuration for encyclopedia project.

Provides centralized access to temporary directories following the style guide
requirement to use Resources.TEMP_DIR.
"""

from pathlib import Path


class Resources:
    """Resource paths and configuration for encyclopedia project"""
    
    # Get project root (go up from encyclopedia/utils/ to project root)
    _project_root = Path(__file__).parent.parent.parent
    TEMP_DIR = Path(_project_root, "temp")
    
    @classmethod
    def get_temp_dir(cls, *subdirs):
        """Get temporary directory with optional subdirectories.
        
        Args:
            *subdirs: Subdirectory path components
            
        Returns:
            Path to temporary directory
            
        Example:
            Resources.get_temp_dir("examples", "create_encyclopedia")
            # Returns: Path(project_root, "temp", "examples", "create_encyclopedia")
        """
        if subdirs:
            return Path(cls.TEMP_DIR, *subdirs)
        return cls.TEMP_DIR
