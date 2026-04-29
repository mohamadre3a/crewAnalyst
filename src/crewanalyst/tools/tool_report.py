from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field





class ConvertMarkdownToPdfInput(BaseModel):
    markdown_path: str = Field(
        default="outputs/report.md",
        description="Path to the markdown file to convert.",
    )
    output_path: str = Field(
        default="outputs/report.pdf",
        description="Where to save the PDF.",
    )


class ConvertMarkdownToPdfTool(BaseTool):
    name: str = "convert_markdown_to_pdf"
    description: str = (
        "Converts a saved markdown report into a styled PDF. Relative image "
        "paths in the markdown resolve correctly so charts embed inline."
    )
    args_schema: Type[BaseModel] = ConvertMarkdownToPdfInput

    def _run(
        self,
        markdown_path: str = "outputs/report.md",
        output_path: str = "outputs/report.pdf",
    ) -> str:
        try:
            import markdown as md_lib
            from weasyprint import HTML, CSS
        except ImportError as e:
            return (
                "ERROR: PDF dependencies missing. Install with: "
                f"pip install markdown weasyprint  (detail: {e})"
            )

        try:
            md_path = Path(markdown_path)
            if not md_path.exists():
                return f"ERROR: markdown file not found at {markdown_path}"

            md_text = md_path.read_text(encoding="utf-8")
            html_body = md_lib.markdown(
                md_text,
                extensions=["tables", "fenced_code", "toc", "sane_lists"],
            )

            css = """
                @page { size: A4; margin: 2cm; }
                body {
                    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
                    line-height: 1.55; color: #1f2937; font-size: 11pt;
                }
                h1 { color: #0f3a5f; border-bottom: 2px solid #0f3a5f;
                     padding-bottom: 6px; margin-top: 0; }
                h2 { color: #1f5c8c; margin-top: 1.6em; border-bottom: 1px solid #e5e7eb;
                     padding-bottom: 4px; }
                h3 { color: #2a6fa8; margin-top: 1.2em; }
                img { max-width: 100%; height: auto; margin: 0.6em 0;
                      page-break-inside: avoid; }
                table { border-collapse: collapse; width: 100%; margin: 1em 0;
                        font-size: 10pt; }
                th, td { border: 1px solid #d1d5db; padding: 6px 10px; text-align: left; }
                th { background: #f3f4f6; }
                code { background: #f3f4f6; padding: 1px 5px; border-radius: 3px;
                       font-size: 0.92em; }
                blockquote { border-left: 3px solid #cbd5e1; margin-left: 0;
                             padding-left: 12px; color: #475569; }
                em { color: #475569; }
            """

            html_doc = (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
                f"<body>{html_body}</body></html>"
            )

            output = Path(output_path)
            if output.is_absolute() or ".." in output.parts:
                return "ERROR: output_path must be a relative path inside the project"
            output.parent.mkdir(parents=True, exist_ok=True)

            # base_url so 'charts/foo.png' resolves relative to the markdown file
            HTML(string=html_doc, base_url=str(md_path.parent.resolve())).write_pdf(
                str(output),
                stylesheets=[CSS(string=css)],
            )
            return str(output)
        except Exception as e:
            return f"ERROR: convert_markdown_to_pdf failed: {e}"


write_markdown_report_tool = WriteMarkdownReportTool()
convert_markdown_to_pdf_tool = ConvertMarkdownToPdfTool()