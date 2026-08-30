from __future__ import annotations

from pathlib import Path
from typing import BinaryIO
from zipfile import BadZipFile, ZipFile

from .base_validator import BaseValidator
from ..formats import SUPPORTED_FORMATS


class ExcelValidationError(ValueError):
    """Raised when an Excel file fails validation."""


class ExcelValidator(BaseValidator):
    """
    Validate Excel files before they are passed to an Excel reader.

    Supported Excel formats:

        .xlsx  -> excel_standard
        .xlsm  -> excel_macro
        .xltx  -> excel_template
        .xltm  -> excel_template_macro
        .xlsb  -> excel_binary
        .xlam  -> excel_addin

    OOXML formats are ZIP-based packages and are structurally
    inspected here.

    XLSB uses a different binary workbook format and therefore
    receives separate validation.
    """

    MAX_FILE_SIZE = 50 * 1024 * 1024

    OOXML_EXTENSIONS = {
        ".xlsx",
        ".xlsm",
        ".xltx",
        ".xltm",
        ".xlam",
    }

    XLSB_EXTENSION = ".xlsb"

    def validate(
        self,
        file_path: str | Path | BinaryIO,
        filename: str | None = None,
        file_size: int | None = None,
    ) -> None:
        """
        Validate an Excel file.

        Validation order:

            1. File exists / object is valid
            2. Filename exists
            3. Extension is supported
            4. File size is valid
            5. File structure is valid
        """

        if file_path is None:
            raise ExcelValidationError(
                "ExcelValidator.validate() requires a file."
            )

        name = (
            filename
            if filename is not None
            else self._get_filename(file_path)
        )

        self.validate_filename(name)

        self.validate_size(
            file_size
            if file_size is not None
            else self._get_file_size(file_path)
        )

        extension = Path(name).suffix.lower()

        if extension in self.OOXML_EXTENSIONS:
            self._validate_ooxml(
                file_path
            )

        elif extension == self.XLSB_EXTENSION:
            self._validate_xlsb(
                file_path
            )

        else:
            raise ExcelValidationError(
                f"Unsupported Excel extension: {extension}"
            )

    # Filename
    def validate_filename(
        self,
        filename: str | None,
    ) -> None:
        """
        Validate the Excel filename and extension.
        """

        if filename is None:
            raise ExcelValidationError(
                "Excel filename is required."
            )

        if not filename.strip():
            raise ExcelValidationError(
                "Excel filename cannot be empty."
            )

        extension = Path(filename).suffix.lower()

        if extension not in SUPPORTED_FORMATS:
            raise ExcelValidationError(
                f"Unsupported file format: "
                f"{extension or 'unknown'}"
            )

        format_type = SUPPORTED_FORMATS[extension]

        if not format_type.startswith("excel_"):
            raise ExcelValidationError(
                "Only Excel files are supported."
            )

    # Size
    def validate_size(
        self,
        file_size: int,
    ) -> None:
        """
        Validate Excel file size.
        """

        if file_size < 0:
            raise ExcelValidationError(
                "Excel file size cannot be negative."
            )

        if file_size > self.MAX_FILE_SIZE:
            raise ExcelValidationError(
                "The maximum Excel file size is 50MB."
            )

    # OOXML validation
    def _validate_ooxml(
        self,
        file_path: str | Path | BinaryIO,
    ) -> None:
        """
        Validate the basic structure of an OOXML workbook.

        OOXML Excel files are ZIP packages. We verify the presence
        of the package metadata and workbook relationship structure.
        """

        try:
            with self._open_zip(file_path) as archive:

                names = set(
                    archive.namelist()
                )

                required_files = {
                    "[Content_Types].xml",
                    "_rels/.rels",
                }

                missing = (
                    required_files - names
                )

                if missing:
                    raise ExcelValidationError(
                        "The Excel OOXML package is missing "
                        "required files."
                    )

                workbook_files = {
                    "xl/workbook.xml",
                    "xl/workbook.bin",
                }

                if not (
                    workbook_files & names
                ):
                    raise ExcelValidationError(
                        "The Excel workbook structure is invalid."
                    )

        except ExcelValidationError:
            raise

        except BadZipFile as exc:
            raise ExcelValidationError(
                "File is not a valid Excel OOXML package."
            ) from exc

        except Exception as exc:
            raise ExcelValidationError(
                f"Unable to validate Excel file: {exc}"
            ) from exc

    # XLSB validation
    def _validate_xlsb(
        self,
        file_path: str | Path | BinaryIO,
    ) -> None:
        """
        Validate an XLSB workbook.

        XLSB is still packaged as an OPC/ZIP container, but its
        workbook content is binary rather than workbook.xml.
        """

        try:
            with self._open_zip(file_path) as archive:

                names = set(
                    archive.namelist()
                )

                required_files = {
                    "[Content_Types].xml",
                    "_rels/.rels",
                }

                missing = (
                    required_files - names
                )

                if missing:
                    raise ExcelValidationError(
                        "The XLSB package is missing "
                        "required files."
                    )

                if "xl/workbook.bin" not in names:
                    raise ExcelValidationError(
                        "The XLSB workbook structure is invalid."
                    )

        except ExcelValidationError:
            raise

        except BadZipFile as exc:
            raise ExcelValidationError(
                "File is not a valid Excel XLSB package."
            ) from exc

        except Exception as exc:
            raise ExcelValidationError(
                f"Unable to validate XLSB file: {exc}"
            ) from exc

    # Helpers
    @staticmethod
    def _open_zip(
        file_path: str | Path | BinaryIO,
    ) -> ZipFile:
        """
        Open an Excel package as a ZIP archive.

        For file-like objects, preserve the original stream position.
        """

        if isinstance(
            file_path,
            (str, Path),
        ):
            return ZipFile(
                file_path,
                "r",
            )

        current_position = file_path.tell()

        try:
            file_path.seek(0)

            archive = ZipFile(
                file_path,
                "r",
            )

            return _PositionPreservingZipFile(
                archive,
                file_path,
                current_position,
            )

        except Exception:
            file_path.seek(
                current_position
            )
            raise

    @staticmethod
    def _get_filename(
        file_path: str | Path | BinaryIO,
    ) -> str:
        """
        Extract a filename from a filesystem path.
        """

        if isinstance(
            file_path,
            (str, Path),
        ):
            return Path(file_path).name

        raise ExcelValidationError(
            "filename is required for file-like objects."
        )

    @staticmethod
    def _get_file_size(
        file_path: str | Path | BinaryIO,
    ) -> int:
        """
        Determine file size when the caller did not provide it.
        """

        if isinstance(
            file_path,
            (str, Path),
        ):
            path = Path(file_path)

            if not path.exists():
                raise ExcelValidationError(
                    "The Excel file does not exist."
                )

            if not path.is_file():
                raise ExcelValidationError(
                    "The Excel path is not a file."
                )

            return path.stat().st_size

        current_position = file_path.tell()

        try:
            file_path.seek(
                0,
                2,
            )

            size = file_path.tell()

        finally:
            file_path.seek(
                current_position
            )

        return size


class _PositionPreservingZipFile:
    """
    Small wrapper that closes the ZIP archive and restores the
    original stream position.
    """

    def __init__(
        self,
        archive: ZipFile,
        file_object: BinaryIO,
        original_position: int,
    ) -> None:
        self.archive = archive
        self.file_object = file_object
        self.original_position = original_position

    def __enter__(self) -> ZipFile:
        return self.archive

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        try:
            self.archive.close()
        finally:
            self.file_object.seek(
                self.original_position
            )