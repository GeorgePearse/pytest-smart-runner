"""Test mapper to determine which tests are affected by code changes."""

import ast
import os
from pathlib import Path
from typing import Set, Dict, List, Optional


class TestMapper:
    """Maps changed source files to their related test files."""

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize the test mapper.

        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = Path(project_root or os.getcwd())
        self.import_map: Dict[Path, Set[Path]] = {}

    def find_test_files(self, test_dirs: Optional[List[str]] = None) -> Set[Path]:
        """
        Find all test files in the project.

        Args:
            test_dirs: List of directories to search for tests. Defaults to ['tests', 'test'].

        Returns:
            Set of Path objects representing test files
        """
        if test_dirs is None:
            test_dirs = ['tests', 'test']

        test_files = set()
        for test_dir in test_dirs:
            test_path = self.project_root / test_dir
            if test_path.exists():
                for test_file in test_path.rglob('test_*.py'):
                    test_files.add(test_file)
                for test_file in test_path.rglob('*_test.py'):
                    test_files.add(test_file)

        return test_files

    def extract_imports(self, file_path: Path) -> Set[str]:
        """
        Extract import statements from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Set of module names imported in the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return set()

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        return imports

    def get_module_path(self, changed_file: Path) -> Optional[str]:
        """
        Convert a file path to its Python module path.

        Args:
            changed_file: Path to the changed file

        Returns:
            Module path as a string (e.g., 'mypackage.module')
        """
        try:
            # Get relative path from project root
            rel_path = changed_file.relative_to(self.project_root)

            # Remove 'src/' prefix if present
            parts = list(rel_path.parts)
            if parts and parts[0] == 'src':
                parts = parts[1:]

            # Remove .py extension and convert to module path
            if parts:
                parts[-1] = parts[-1].replace('.py', '')
                return '.'.join(parts)
        except ValueError:
            return None

        return None

    def find_affected_tests(
        self,
        changed_files: Set[Path],
        test_files: Optional[Set[Path]] = None
    ) -> Set[Path]:
        """
        Find test files affected by the changed source files.

        Args:
            changed_files: Set of changed source files
            test_files: Set of test files to check. If None, will discover automatically.

        Returns:
            Set of test files that should be run
        """
        if test_files is None:
            test_files = self.find_test_files()

        affected_tests = set()

        # Strategy 1: Direct test file changes
        for changed_file in changed_files:
            if self._is_test_file(changed_file):
                affected_tests.add(changed_file)

        # Strategy 2: Naming convention mapping (test_foo.py tests foo.py)
        for changed_file in changed_files:
            if not self._is_test_file(changed_file):
                # Try to find corresponding test file
                test_candidates = self._get_test_candidates(changed_file)
                for candidate in test_candidates:
                    if candidate in test_files:
                        affected_tests.add(candidate)

        # Strategy 3: Import analysis - find tests that import the changed modules
        changed_modules = set()
        for changed_file in changed_files:
            module_path = self.get_module_path(changed_file)
            if module_path:
                changed_modules.add(module_path)

        for test_file in test_files:
            imports = self.extract_imports(test_file)
            # Check if any changed module is imported
            for changed_module in changed_modules:
                module_root = changed_module.split('.')[0]
                if module_root in imports:
                    affected_tests.add(test_file)
                    break

        return affected_tests

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file based on naming convention."""
        name = file_path.name
        return name.startswith('test_') or name.endswith('_test.py')

    def _get_test_candidates(self, source_file: Path) -> List[Path]:
        """
        Get potential test files for a given source file.

        Args:
            source_file: Path to the source file

        Returns:
            List of potential test file paths
        """
        candidates = []
        filename = source_file.stem  # filename without extension

        # Common test naming patterns
        patterns = [
            f"test_{filename}.py",
            f"{filename}_test.py",
        ]

        # Check in tests directory
        for test_dir in ['tests', 'test']:
            test_path = self.project_root / test_dir
            if test_path.exists():
                for pattern in patterns:
                    candidate = test_path / pattern
                    candidates.append(candidate)

                    # Also check in subdirectories matching source structure
                    try:
                        rel_path = source_file.relative_to(self.project_root)
                        # Remove src prefix if present
                        parts = list(rel_path.parts)
                        if parts and parts[0] == 'src':
                            parts = parts[1:]
                        if len(parts) > 1:
                            # Reconstruct path in test directory
                            subdir = Path(*parts[:-1])
                            candidate = test_path / subdir / pattern
                            candidates.append(candidate)
                    except ValueError:
                        pass

        return candidates
