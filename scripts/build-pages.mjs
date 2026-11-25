import {cp, mkdir, readFile, readdir, rm, writeFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";

const projectRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);
const courseRoot = path.join(projectRoot, "Computer-Graphics");
const outputDirectory = process.env.PAGES_OUTPUT;
const configuredBaseUrl = process.env.PAGES_BASE_URL;

if (!outputDirectory || !configuredBaseUrl) {
    throw new Error(
        "Set PAGES_OUTPUT and PAGES_BASE_URL before building the Pages site.",
    );
}

const outputPath = path.resolve(outputDirectory);
if (
    outputPath === projectRoot ||
    projectRoot.startsWith(`${outputPath}${path.sep}`)
) {
    throw new Error(
        "PAGES_OUTPUT must not point to the project root or one of its parents.",
    );
}

const siteUrl = new URL(configuredBaseUrl);
if (!siteUrl.pathname.endsWith("/")) siteUrl.pathname += "/";

await rm(outputPath, {recursive: true, force: true});
await mkdir(outputPath, {recursive: true});

function includeSource(sourcePath) {
    const relativePath = path.relative(projectRoot, sourcePath);
    const segments = relativePath.split(path.sep);
    return (
        !segments.some((segment) =>
            [".git", ".venv", "__pycache__", "node_modules"].includes(segment),
        ) && !relativePath.endsWith(".pyc")
    );
}

const filesAndDirectories = ["index.html", "robots.txt", "assets"];

for (const relativePath of filesAndDirectories) {
    await cp(
        path.join(projectRoot, relativePath),
        path.join(outputPath, relativePath),
        {recursive: true, filter: includeSource},
    );
}

const courseFilesAndDirectories = [
    "Syllabus.pdf",
    "Computer_Graphics_Numerical_Question_Bank_1.pdf",
    "Lectures",
    "Resources",
];

const courseOutputPath = path.join(outputPath, "Computer-Graphics");
await mkdir(courseOutputPath, {recursive: true});

for (const relativePath of courseFilesAndDirectories) {
    await cp(
        path.join(courseRoot, relativePath),
        path.join(courseOutputPath, relativePath),
        {recursive: true, filter: includeSource},
    );
}

const indexPath = path.join(outputPath, "index.html");
const indexHtml = await readFile(indexPath, "utf8");
await writeFile(indexPath, indexHtml.replaceAll("__SITE_URL__", siteUrl.href));

const robotsPath = path.join(outputPath, "robots.txt");
const robotsTxt = await readFile(robotsPath, "utf8");
await writeFile(robotsPath, robotsTxt.replaceAll("__SITE_URL__", siteUrl.href));

async function findPdfs(directory, relativeDirectory = "") {
    const pdfPaths = [];
    for (const entry of await readdir(directory, {withFileTypes: true})) {
        const relativePath = path.posix.join(relativeDirectory, entry.name);
        const fullPath = path.join(directory, entry.name);
        if (entry.isDirectory()) {
            pdfPaths.push(...(await findPdfs(fullPath, relativePath)));
        } else if (
            entry.isFile() &&
            entry.name.toLowerCase().endsWith(".pdf")
        ) {
            pdfPaths.push(relativePath);
        }
    }
    return pdfPaths;
}

function escapeXml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

const pdfPaths = await findPdfs(outputPath);
const urls = [
    siteUrl.href,
    ...pdfPaths.map((relativePath) => {
        const encodedPath = relativePath
            .split("/")
            .map(encodeURIComponent)
            .join("/");
        return new URL(encodedPath, siteUrl).href;
    }),
];
const sitemap = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls.map((url) => `  <url><loc>${escapeXml(url)}</loc></url>`),
    "</urlset>",
    "",
].join("\n");

await writeFile(path.join(outputPath, "sitemap.xml"), sitemap);
console.log(`Built ${urls.length} crawlable URLs in ${outputPath}`);
