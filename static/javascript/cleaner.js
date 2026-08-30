document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const dropzone = document.getElementById("dropzone");
    const input = document.getElementById("file-input");
    const filenameEl = document.getElementById("dz-filename");
    const submitBtn = document.getElementById("upload-submit");

    if (!dropzone || !input || !filenameEl || !submitBtn) {
        return;
    }

    const MAX_FILE_SIZE = 50 * 1024 * 1024;

    const SUPPORTED_TYPES = {
        csv: {
            extension: ".csv",
            label: "CSV",
        },
        xlsx: {
            extension: ".xlsx",
            label: "Excel",
        },
    };


    function getExtension(filename) {
        const lastDot = filename.lastIndexOf(".");

        if (lastDot === -1) {
            return "";
        }

        return filename
            .slice(lastDot)
            .toLowerCase();
    }


    function getFileType(file) {
        const extension = getExtension(file.name);

        return Object.values(SUPPORTED_TYPES).find(
            (type) => type.extension === extension
        ) || null;
    }


    function formatFileSize(bytes) {
        if (bytes < 1024) {
            return `${bytes} B`;
        }

        if (bytes < 1024 * 1024) {
            return `${Math.round(bytes / 1024)} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }


    function setFilenameMessage(message, isError = false) {
        filenameEl.textContent = message;

        filenameEl.classList.add("is-visible");

        filenameEl.classList.toggle("is-error", isError);

        submitBtn.disabled = isError;
    }


    function clearFileState() {
        filenameEl.textContent = "";
        filenameEl.classList.remove(
            "is-visible",
            "is-error"
        );

        submitBtn.disabled = true;
    }


    function validateFile(file) {
        if (!file) {
            return {
                valid: false,
                message: "Please select a file.",
            };
        }

        const fileType = getFileType(file);

        if (!fileType) {
            return {
                valid: false,
                message: "Unsupported file type. Please choose a CSV or Excel (.xlsx) file.",
            };
        }

        if (file.size > MAX_FILE_SIZE) {
            return {
                valid: false,
                message: "File is too large. The maximum allowed size is 50MB.",
            };
        }

        return {
            valid: true,
            type: fileType,
        };
    }


    function showFile(file) {
        const validation = validateFile(file);

        if (!validation.valid) {
            setFilenameMessage(
                validation.message,
                true
            );

            return;
        }

        const fileType = validation.type;

        filenameEl.textContent =
            `${file.name} — ${formatFileSize(file.size)} — ${fileType.label}`;

        filenameEl.classList.add("is-visible");
        filenameEl.classList.remove("is-error");

        submitBtn.disabled = false;
    }


    function openFilePicker() {
        input.click();
    }


    /*Clicking the dropzone opens the native file picker. */
    dropzone.addEventListener("click", (event) => {
        if (event.target === input) {
            return;
        }

        openFilePicker();
    });


    /*Keyboard accessibility.*/
    dropzone.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openFilePicker();
        }
    });


    /*Normal file selection.*/
    input.addEventListener("change", () => {
        const file = input.files && input.files[0];

        if (!file) {
            clearFileState();
            return;
        }

        showFile(file);
    });


    /* Drag and drop — prevent the browser from opening dropped files directly.*/
    ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();

            dropzone.classList.add("is-dragover");
        });
    });


    ["dragleave", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();

            dropzone.classList.remove("is-dragover");
        });
    });


    /*Handle dropped files.*/
    dropzone.addEventListener("drop", (event) => {
        const files = event.dataTransfer.files;

        if (!files || !files.length) {
            clearFileState();
            return;
        }

        const file = files[0];

        /* Only one dataset is processed per upload.*/
        if (files.length > 1) {
            setFilenameMessage(
                "Please drop one file at a time.",
                true
            );

            return;
        }

        /*Assign the dropped file to the real input so that Django receives it during form submission.*/
        try {
            const dataTransfer = new DataTransfer();

            dataTransfer.items.add(file);

            input.files = dataTransfer.files;
        } catch (error) {
            /*
             * Some older browsers may not allow assigning
             * FileList programmatically. Validation still
             * runs and the normal picker remains available.
             */
            console.warn(
                "Could not assign dropped file to input.",
                error
            );
        }

        showFile(file);
    });


    /*
     * Prevent accidental browser navigation when a file is
     * dragged over the page outside the dropzone.
     */
    document.addEventListener("dragover", (event) => {
        event.preventDefault();
    });


    document.addEventListener("drop", (event) => {
        if (!dropzone.contains(event.target)) {
            event.preventDefault();
        }
    });


    /*
     * Initial state.
     */
    clearFileState();
});

