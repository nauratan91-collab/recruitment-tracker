import os
import shutil
import zipfile

def package_docs():
    doc_src = r"C:\Users\ITkey\.gemini\antigravity\brain\592c92cc-8ce2-4e27-b260-6cfb4dc94609\DOCUMENTATION.md"
    desktop = r"C:\Users\ITkey\OneDrive - Key Dynamics Solutions Private Limited\Desktop"
    downloads = r"C:\Users\ITkey\Downloads"
    proj_dir = r"C:\Users\ITkey\.gemini\antigravity\scratch\job-requirement-tracker"
    dist_dir = os.path.join(proj_dir, "dist_website")

    # Copy markdown doc
    shutil.copy2(doc_src, os.path.join(desktop, "DOCUMENTATION.md"))
    shutil.copy2(doc_src, os.path.join(downloads, "DOCUMENTATION.md"))
    shutil.copy2(doc_src, os.path.join(proj_dir, "DOCUMENTATION.md"))
    if os.path.exists(dist_dir):
        shutil.copy2(doc_src, os.path.join(dist_dir, "DOCUMENTATION.md"))

    print("Copied DOCUMENTATION.md to Desktop, Downloads, and dist_website")

    with open(doc_src, "r", encoding="utf-8") as f:
        doc_text = f.read()

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Key Dynamics Solutions - End-to-End System & User Guide</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @media print {{
            .no-print {{ display: none !important; }}
            body {{ font-size: 11pt; padding: 0 !important; background: white !important; }}
        }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 p-6 sm:p-12 max-w-5xl mx-auto font-sans">
    <div class="no-print mb-6 flex justify-between items-center bg-indigo-50 border border-indigo-200 p-4 rounded-xl shadow-sm">
        <div class="flex items-center space-x-2">
            <i class="fa-solid fa-book-bookmark text-indigo-600 text-lg"></i>
            <span class="text-sm font-bold text-indigo-900">Key Dynamics Solutions — User & Admin Manual</span>
        </div>
        <button onclick="window.print()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow transition flex items-center space-x-1.5">
            <i class="fa-solid fa-print"></i>
            <span>Print / Save as PDF</span>
        </button>
    </div>
    <div class="bg-white p-8 sm:p-14 rounded-2xl shadow-sm border border-slate-200">
        <pre style="white-space: pre-wrap; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #1e293b;">{doc_text}</pre>
    </div>
</body>
</html>"""

    with open(os.path.join(desktop, "DOCUMENTATION.html"), "w", encoding="utf-8") as f:
        f.write(html_doc)
    with open(os.path.join(downloads, "DOCUMENTATION.html"), "w", encoding="utf-8") as f:
        f.write(html_doc)
    if os.path.exists(dist_dir):
        with open(os.path.join(dist_dir, "DOCUMENTATION.html"), "w", encoding="utf-8") as f:
            f.write(html_doc)

    print("Generated styled DOCUMENTATION.html on Desktop and Downloads")

    # Rebuild ZIP with DOCUMENTATION files included
    zip_path = os.path.join(proj_dir, "key-dynamics-recruitment-portal.zip")
    if os.path.exists(dist_dir):
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, dist_dir)
                    z.write(full_p, rel_p)

        shutil.copy2(zip_path, os.path.join(downloads, "key-dynamics-recruitment-portal.zip"))
        shutil.copy2(zip_path, os.path.join(desktop, "key-dynamics-recruitment-portal.zip"))
        print("Updated key-dynamics-recruitment-portal.zip with documentation included!")

if __name__ == '__main__':
    package_docs()
