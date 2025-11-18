import pathlib


class Path(pathlib.Path):
    def existsi(self, *, follow_symlinks=True) -> bool:
        """
        Returns True if the given path exists, using a case-insensitive lookup.
        Each parent directory is resolved case-insensitively, and then the final
        file/directory is checked the same way.
        """
        parts = self.expanduser().parts

        # Start with root or drive ("/", "C:\", etc.)
        current = Path(parts[0])

        for part in parts[1:]:
            if not current.exists():
                return False

            # Scan children of current directory for case-insensitive match
            matched = None
            try:
                for child in current.iterdir():
                    if child.name.lower() == part.lower():
                        matched = child
                        break
            except PermissionError:
                return False

            if matched is None:
                return False

            current = matched

        return current.exists()
