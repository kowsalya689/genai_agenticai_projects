/**
 * MNIST Autoencoder — frontend logic.
 * Handles drag-and-drop upload, preview, calling /api/reconstruct,
 * rendering results, and error/loading states.
 */

(function () {
    "use strict";

    const API_RECONSTRUCT_URL = "/api/reconstruct";

    // --- Element references -------------------------------------------------
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    const dropzoneIdle = document.getElementById("dropzone-idle");
    const dropzoneSelected = document.getElementById("dropzone-selected");
    const previewThumb = document.getElementById("preview-thumb");
    const selectedFilename = document.getElementById("selected-filename");
    const removeFileBtn = document.getElementById("remove-file-btn");

    const reconstructBtn = document.getElementById("reconstruct-btn");
    const btnLabel = reconstructBtn.querySelector(".btn-label");
    const btnSpinner = reconstructBtn.querySelector(".btn-spinner");
    const statusLine = document.getElementById("status-line");

    const resultCard = document.getElementById("result-card");
    const originalOutput = document.getElementById("original-output");
    const reconstructedOutput = document.getElementById("reconstructed-output");
    const originalDims = document.getElementById("original-dims");
    const reconstructedDims = document.getElementById("reconstructed-dims");

    const tryAnotherBtn = document.getElementById("try-another-btn");
    const downloadBtn = document.getElementById("download-btn");

    const toast = document.getElementById("toast");

    const ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "jfif"];
    const MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024;

    let selectedFile = null;
    let toastTimer = null;
    let lastReconstructedDataUrl = null;

    // --- Dropzone interactions -----------------------------------------------

    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            fileInput.click();
        }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "dragend", "drop"].forEach((eventName) => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", (event) => {
        const files = event.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    fileInput.addEventListener("change", (event) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    removeFileBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        clearSelection();
    });

    // --- Selection / validation -----------------------------------------------

    function handleFileSelection(file) {
        const extension = file.name.split(".").pop().toLowerCase();

        if (!ALLOWED_EXTENSIONS.includes(extension)) {
            showToast("Unsupported file type. Please choose a PNG, JPG, JPEG, WEBP, or JFIF image.");
            return;
        }

        if (file.size > MAX_FILE_SIZE_BYTES) {
            showToast("That file is too large. Please choose an image under 8 MB.");
            return;
        }

        selectedFile = file;
        setStatus("", null);
        hideResults();

        const reader = new FileReader();
        reader.onload = (e) => {
            previewThumb.src = e.target.result;
            selectedFilename.textContent = file.name;
            dropzoneIdle.classList.add("hidden");
            dropzoneSelected.classList.remove("hidden");
            reconstructBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function clearSelection() {
        selectedFile = null;
        fileInput.value = "";
        previewThumb.src = "";
        selectedFilename.textContent = "";
        dropzoneSelected.classList.add("hidden");
        dropzoneIdle.classList.remove("hidden");
        reconstructBtn.disabled = true;
        setStatus("", null);
        hideResults();
    }

    // --- Reconstruct flow -----------------------------------------------

    reconstructBtn.addEventListener("click", async () => {
        if (!selectedFile) {
            return;
        }

        setLoading(true);
        setStatus("Reconstructing image...", null);
        hideResults();

        const formData = new FormData();
        formData.append("image", selectedFile);

        try {
            const response = await fetch(API_RECONSTRUCT_URL, {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const message = (data && data.error) || "The image could not be reconstructed. Please try again.";
                setStatus("", null);
                showToast(message);
                return;
            }

            renderResults(data);
            setStatus("Reconstruction complete.", "success");
        } catch (error) {
            setStatus("", null);
            showToast("Could not reach the server. Please check your connection and try again.");
        } finally {
            setLoading(false);
        }
    });

    function renderResults(data) {
        originalOutput.src = data.original_image;
        reconstructedOutput.src = data.reconstructed_image;
        lastReconstructedDataUrl = data.reconstructed_image;

        const dims = data.dimensions || { width: 28, height: 28 };
        const dimsText = `${dims.width} × ${dims.height}px`;
        originalDims.textContent = dimsText;
        reconstructedDims.textContent = dimsText;

        resultCard.classList.remove("hidden");
        resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function hideResults() {
        resultCard.classList.add("hidden");
    }

    // --- Result actions -----------------------------------------------

    tryAnotherBtn.addEventListener("click", () => {
        clearSelection();
        dropzone.scrollIntoView({ behavior: "smooth", block: "center" });
    });

    downloadBtn.addEventListener("click", () => {
        if (!lastReconstructedDataUrl) {
            return;
        }
        const link = document.createElement("a");
        link.href = lastReconstructedDataUrl;
        link.download = "reconstructed.png";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // --- UI helpers -----------------------------------------------

    function setLoading(isLoading) {
        reconstructBtn.disabled = isLoading || !selectedFile;
        btnLabel.textContent = isLoading ? "Reconstructing..." : "Reconstruct image";
        btnSpinner.classList.toggle("hidden", !isLoading);
    }

    function setStatus(message, tone) {
        statusLine.textContent = message;
        if (tone) {
            statusLine.setAttribute("data-tone", tone);
        } else {
            statusLine.removeAttribute("data-tone");
        }
    }

    function showToast(message) {
        toast.textContent = message;
        toast.classList.add("visible");

        if (toastTimer) {
            clearTimeout(toastTimer);
        }
        toastTimer = setTimeout(() => {
            toast.classList.remove("visible");
        }, 4500);
    }
})();
