const searchInput = document.querySelector("#resource-search-input");
const groupFilter = document.querySelector("#group-filter");
const resultCount = document.querySelector("#result-count");
const noResults = document.querySelector("#no-results");
const entries = [...document.querySelectorAll("[data-index-group]")];
const catalogSections = [
    ...document.querySelectorAll("[data-catalog-section]"),
];
const pdfViewer = document.querySelector("#pdf-viewer");
const pdfViewerTitle = document.querySelector("#pdf-viewer-title");
const pdfViewerFrame = document.querySelector(".pdf-viewer-frame");
const pdfViewerNewTab = document.querySelector("#pdf-viewer-new-tab");
const pdfViewerClose = document.querySelector("#pdf-viewer-close");

for (const link of document.querySelectorAll(".resource-link[href]")) {
    if (!new URL(link.href).pathname.toLocaleLowerCase().endsWith(".pdf")) {
        continue;
    }

    link.querySelector(".resource-open").textContent = "Open in new tab ↗";

    const title = link
        .querySelector(".resource-title")
        .textContent.replace(/\s+/g, " ")
        .trim();
    const previewButton = document.createElement("button");
    previewButton.className = "resource-preview";
    previewButton.type = "button";
    previewButton.textContent = "Preview";
    previewButton.setAttribute("aria-label", `Preview ${title}`);
    link.closest("li").classList.add("pdf-resource");
    link.insertAdjacentElement("afterend", previewButton);

    previewButton.addEventListener("click", () => {
        pdfViewerTitle.textContent = title;
        pdfViewerFrame.title = `${title} PDF preview`;
        pdfViewerFrame.src = link.href;
        pdfViewerNewTab.href = link.href;
        pdfViewer.showModal();
    });
}

pdfViewerClose.addEventListener("click", () => pdfViewer.close());
pdfViewer.addEventListener("close", () => {
    pdfViewerFrame.removeAttribute("src");
});

function updateCatalog() {
    const query = searchInput.value.trim().toLocaleLowerCase();
    const selectedGroup = groupFilter.value;
    let visibleCount = 0;

    for (const entry of entries) {
        const text =
            `${entry.textContent} ${entry.dataset.keywords ?? ""}`.toLocaleLowerCase();
        const matchesText = query === "" || text.includes(query);
        const matchesGroup =
            selectedGroup === "all" ||
            entry.dataset.indexGroup === selectedGroup;
        entry.hidden = !(matchesText && matchesGroup);
        if (!entry.hidden) visibleCount += 1;
    }

    for (const section of catalogSections) {
        section.hidden = !section.querySelector(
            "[data-index-group]:not([hidden])",
        );
    }

    noResults.hidden = visibleCount > 0;
    resultCount.textContent = `${visibleCount} of ${entries.length} resources shown`;
}

searchInput.addEventListener("input", updateCatalog);
groupFilter.addEventListener("change", updateCatalog);
updateCatalog();
