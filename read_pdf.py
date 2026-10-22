from pypdf import PdfReader

reader = PdfReader("docs/form18a.pdf")
print(f"{len(reader.pages)} pages\n")

for page_number, page in enumerate(reader.pages, start=1):
    text = page.extract_text()
    print(f"--- Page {page_number}: {len(text)} characters ---")
    print(text[:300])   # first 300 characters of each page
    print()