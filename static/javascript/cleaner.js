document.addEventListener("DOMContentLoaded", function () {

    const dropzone = document.getElementById("dropzone");
    const input = document.getElementById("csv-input");
    const filenameEl = document.getElementById("dz-filename");
    const submitBtn = document.getElementById("upload-submit");


    if (!dropzone || !input) {
        return;
    }


    function showFile(file) {

        if (!file) {
            return;
        }

        const sizeKb = Math.round(file.size / 1024);

        filenameEl.textContent =
            `${file.name} — ${sizeKb.toLocaleString()} KB`;

        filenameEl.classList.add("is-visible");

        if (submitBtn) {
            submitBtn.disabled = false;
        }
    }


    // Click dropzone to open file browser
    dropzone.addEventListener("click", function () {
        input.click();
    });


    // Keyboard accessibility
    dropzone.addEventListener("keydown", function (event) {

        if (event.key === "Enter" || event.key === " ") {

            event.preventDefault();

            input.click();
        }
    });


    // File selected normally
    input.addEventListener("change", function () {

        if (input.files && input.files[0]) {

            const file = input.files[0];

            if (!file.name.toLowerCase().endsWith(".csv")) {

                filenameEl.textContent =
                    "Only .csv files are accepted.";

                filenameEl.classList.add("is-visible");

                submitBtn.disabled = true;

                return;
            }

            showFile(file);
        }
    });


    // Drag over
    ["dragenter", "dragover"].forEach(function (eventName) {

        dropzone.addEventListener(eventName, function (event) {

            event.preventDefault();

            dropzone.classList.add("is-dragover");
        });
    });


    // Drag leave / drop
    ["dragleave", "drop"].forEach(function (eventName) {

        dropzone.addEventListener(eventName, function (event) {

            event.preventDefault();

            dropzone.classList.remove("is-dragover");
        });
    });


    // Drop file
    dropzone.addEventListener("drop", function (event) {

        const file =
            event.dataTransfer.files &&
            event.dataTransfer.files[0];


        if (!file) {
            return;
        }


        if (!file.name.toLowerCase().endsWith(".csv")) {

            filenameEl.textContent =
                "Only .csv files are accepted.";

            filenameEl.classList.add("is-visible");

            submitBtn.disabled = true;

            return;
        }


        input.files = event.dataTransfer.files;

        showFile(file);
    });

});