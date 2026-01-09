from pathlib import Path
import contextlib
import io

def extract_text(storage_path: str) -> str:
    p = Path(storage_path)
    suffix = p.suffix.lower()

    if suffix in {".txt", ".md"}:
        return p.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        from pypdf import PdfReader

        parts: list[str] = []

        # Suppress noisy pypdf stderr output
        with contextlib.redirect_stderr(io.StringIO()):
            reader = PdfReader(str(p))
            for page in reader.pages:
                parts.append(page.extract_text() or "")

        return "\n".join(parts)

    raise ValueError(f"Unsupported file type: {suffix}")
