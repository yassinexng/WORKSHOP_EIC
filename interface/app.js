document.addEventListener("DOMContentLoaded", function () {
    const documentsList = document.getElementById("documents-list");
    const documentsLoading = document.getElementById("documents-loading");
    const ragForm = document.getElementById("rag-form");
    const questionInput = document.getElementById("question-input");
    const submitBtn = document.getElementById("submit-btn");
    const clearBtn = document.getElementById("clear-btn");
    const btnText = document.getElementById("btn-text");
    const loadingIndicator = document.getElementById("loading-indicator");
    const errorMessage = document.getElementById("error-message");
    const emptyState = document.getElementById("empty-state");
    const responsePanel = document.getElementById("response-panel");
    const answerText = document.getElementById("answer-text");
    const sourcesList = document.getElementById("sources-list");

    const uploadForm = document.getElementById("upload-form");
    const pdfFileInput = document.getElementById("pdf-file-input");
    const uploadBtn = document.getElementById("upload-btn");
    const uploadBtnText = document.getElementById("upload-btn-text");
    const uploadLoading = document.getElementById("upload-loading");
    const uploadMessage = document.getElementById("upload-message");
    const uploadError = document.getElementById("upload-error");

    function fetchDocuments() {
        fetch("/api/documents")
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Erreur de recuperation des documents.");
                }
                return response.json();
            })
            .then(function (data) {
                documentsList.textContent = "";
                const docs = data.documents || [];
                if (docs.length === 0) {
                    documentsLoading.textContent = "Aucun document PDF charge.";
                    documentsLoading.hidden = false;
                    documentsList.hidden = true;
                    return;
                }
                documentsLoading.hidden = true;
                documentsList.hidden = false;
                docs.forEach(function (docName) {
                    const li = document.createElement("li");
                    li.className = "document-badge";

                    const nameSpan = document.createElement("span");
                    nameSpan.className = "document-name";
                    nameSpan.textContent = docName;

                    const delBtn = document.createElement("button");
                    delBtn.type = "button";
                    delBtn.className = "document-delete-btn";
                    delBtn.setAttribute("aria-label", "Supprimer " + docName);
                    delBtn.textContent = "\u00D7";
                    delBtn.addEventListener("click", function () {
                        deleteDocument(docName, li);
                    });

                    li.appendChild(nameSpan);
                    li.appendChild(delBtn);
                    documentsList.appendChild(li);
                });
            })
            .catch(function () {
                documentsLoading.textContent = "Impossible de charger la liste des documents.";
                documentsLoading.hidden = false;
            });
    }

    function clearError() {
        errorMessage.hidden = true;
        errorMessage.textContent = "";
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.hidden = false;
    }

    function setLoading(isLoading) {
        submitBtn.disabled = isLoading;
        clearBtn.disabled = isLoading;
        questionInput.disabled = isLoading;
        if (isLoading) {
            btnText.textContent = "Recherche en cours...";
            loadingIndicator.hidden = false;
            clearError();
        } else {
            btnText.textContent = "Envoyer la question";
            loadingIndicator.hidden = true;
        }
    }

    function setUploadLoading(isLoading) {
        uploadBtn.disabled = isLoading;
        pdfFileInput.disabled = isLoading;
        if (isLoading) {
            uploadBtnText.textContent = "Traitement en cours...";
            uploadLoading.hidden = false;
            uploadMessage.hidden = true;
            uploadError.hidden = true;
        } else {
            uploadBtnText.textContent = "Importer et indexer le cours";
            uploadLoading.hidden = true;
        }
    }

    function handleSubmit(event) {
        if (event) {
            event.preventDefault();
        }
        const question = questionInput.value.trim();
        if (!question) {
            showError("Veuillez saisir une question avant de soumettre.");
            return;
        }

        setLoading(true);

        fetch("/api/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: question })
        })
            .then(function (response) {
                return response.json().then(function (payload) {
                    if (!response.ok) {
                        throw new Error(payload.error || "Une erreur est survenue.");
                    }
                    return payload;
                });
            })
            .then(function (data) {
                emptyState.hidden = true;
                responsePanel.hidden = false;

                const rawAnswer = data.answer || "";
                const answerLines = rawAnswer.split("\n\n");
                const mainAnswer = answerLines[0].trim();
                answerText.textContent = mainAnswer;

                sourcesList.textContent = "";
                const sources = data.sources || [];
                if (sources.length === 0) {
                    const noSourceLi = document.createElement("li");
                    noSourceLi.className = "source-item source-item--empty";
                    noSourceLi.textContent = "Aucun passage source directement cite.";
                    sourcesList.appendChild(noSourceLi);
                } else {
                    sources.forEach(function (src) {
                        const li = document.createElement("li");
                        li.className = "source-item";

                        const headerDiv = document.createElement("div");
                        headerDiv.className = "source-header";

                        const badgeSpan = document.createElement("span");
                        badgeSpan.className = "source-badge";
                        badgeSpan.textContent = src.source;

                        const pageSpan = document.createElement("span");
                        pageSpan.className = "source-page";
                        pageSpan.textContent = "Page " + src.page;

                        const scoreSpan = document.createElement("span");
                        scoreSpan.className = "source-score";
                        scoreSpan.textContent = "Score " + (1 - src.distance).toFixed(2);

                        headerDiv.appendChild(badgeSpan);
                        headerDiv.appendChild(pageSpan);
                        headerDiv.appendChild(scoreSpan);

                        const quoteDiv = document.createElement("blockquote");
                        quoteDiv.className = "source-quote";
                        quoteDiv.textContent = src.text;

                        li.appendChild(headerDiv);
                        li.appendChild(quoteDiv);
                        sourcesList.appendChild(li);
                    });
                }
            })
            .catch(function (err) {
                showError(err.message || "Impossible de contacter l'assistant.");
            })
            .finally(function () {
                setLoading(false);
            });
    }

    function handleUpload(event) {
        if (event) {
            event.preventDefault();
        }
        if (!pdfFileInput.files || pdfFileInput.files.length === 0) {
            uploadError.textContent = "Veuillez selectionner un fichier PDF.";
            uploadError.hidden = false;
            return;
        }
        const file = pdfFileInput.files[0];
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            uploadError.textContent = "Seuls les fichiers PDF (.pdf) sont acceptes.";
            uploadError.hidden = false;
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        setUploadLoading(true);

        fetch("/api/upload", {
            method: "POST",
            body: formData
        })
            .then(function (response) {
                return response.json().then(function (payload) {
                    if (!response.ok) {
                        throw new Error(payload.error || "Erreur lors de l'envoi du fichier.");
                    }
                    return payload;
                });
            })
            .then(function (data) {
                uploadMessage.textContent = data.message || "Document importe et indexe avec succes.";
                uploadMessage.hidden = false;
                pdfFileInput.value = "";
                fetchDocuments();
            })
            .catch(function (err) {
                uploadError.textContent = err.message || "Impossible d'importer le fichier.";
                uploadError.hidden = false;
            })
            .finally(function () {
                setUploadLoading(false);
            });
    }

    function deleteDocument(docName, listItem) {
        listItem.setAttribute("aria-busy", "true");
        listItem.style.opacity = "0.5";
        fetch("/api/documents/" + encodeURIComponent(docName), { method: "DELETE" })
            .then(function (response) {
                return response.json().then(function (payload) {
                    if (!response.ok) {
                        throw new Error(payload.error || "Erreur lors de la suppression.");
                    }
                    return payload;
                });
            })
            .then(function () {
                fetchDocuments();
            })
            .catch(function (err) {
                listItem.removeAttribute("aria-busy");
                listItem.style.opacity = "";
                alert(err.message || "Impossible de supprimer le document.");
            });
    }

    ragForm.addEventListener("submit", handleSubmit);

    if (uploadForm) {
        uploadForm.addEventListener("submit", handleUpload);
    }

    questionInput.addEventListener("keydown", function (e) {
        if (e.ctrlKey && e.key === "Enter") {
            e.preventDefault();
            handleSubmit();
        }
    });

    clearBtn.addEventListener("click", function () {
        questionInput.value = "";
        clearError();
        questionInput.focus();
    });

    fetchDocuments();
});
