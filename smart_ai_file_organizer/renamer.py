"""
renamer.py
----------
AI Smart Rename — uses NVIDIA NIM API (free) to generate meaningful
filenames from document content.

Uses the OpenAI-compatible NVIDIA API endpoint with meta/llama-3.1-8b-instruct.

Setup
-----
1. Get free API key: https://build.nvidia.com/models
2. Add to config.json:
   "smart_rename": {
       "enabled": false,
       "api_key": "nvapi-your-key-here"
   }

Examples
--------
  scan0023.pdf              → Invoice_Amazon_Mar2024_1299.pdf
  doc_final_v3.docx         → Resume_Sara_Python_Developer.docx
  untitled_notes.txt        → AI_Transformer_Research_Notes.txt
  file_1234.pdf             → Medical_BloodTest_Report_Jan2026.pdf
"""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL    = "meta/llama-3.1-8b-instruct"

RENAME_PROMPT = """You are a file naming assistant. Read the document excerpt and suggest a clean descriptive filename.

Rules:
- Maximum 5 words separated by underscores
- Include: document type + key entity/name + date or amount if visible
- No spaces, no special characters except underscores
- Title_Case each word
- Do NOT include the file extension
- Return ONLY the filename, nothing else, no explanation

Examples:
- Invoice_Amazon_Mar2024_1299
- Resume_Sara_Python_Developer
- Medical_BloodTest_Report_Jan2026
- AI_Transformer_Research_Notes
- Legal_NDA_Contract_Acme

Document excerpt:
{text}

Filename:"""


class SmartRenamer:
    """
    Uses NVIDIA NIM API (free) to generate smart filenames.

    Parameters
    ----------
    api_key : str  — NVIDIA API key (nvapi-...)
                     Get free key: https://build.nvidia.com/models
    enabled : bool — if False, renaming is skipped
    """

    def __init__(self, api_key: str = "", enabled: bool = True):
        self.enabled = enabled
        self._client = None

        if not enabled:
            return

        key = api_key or os.environ.get("NVIDIA_API_KEY", "")

        if not key:
            logger.warning(
                "No NVIDIA API key found — Smart Rename disabled.\n"
                "  Get free key: https://build.nvidia.com/models\n"
                "  Add to config.json → smart_rename → api_key"
            )
            self.enabled = False
            return

        try:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=NVIDIA_BASE_URL,
                api_key=key,
            )
            logger.info("Smart Rename ready ✓ (NVIDIA API — %s)", NVIDIA_MODEL)
        except ImportError:
            logger.warning(
                "openai package not installed — Smart Rename disabled.\n"
                "Run: pip install openai"
            )
            self.enabled = False

    def rename(self, original_filename: str, text: str) -> str:
        """
        Generate a smart filename from document content.

        Parameters
        ----------
        original_filename : original file name (e.g. 'scan0023.pdf')
        text              : extracted text content of the file

        Returns
        -------
        New filename with original extension (e.g. 'Invoice_Amazon_Mar2024.pdf')
        Returns original filename if rename fails or is disabled.
        """
        if not self.enabled or not self._client:
            return original_filename

        if not text or len(text.strip()) < 20:
            logger.debug("Too little text to rename '%s' — keeping original.", original_filename)
            return original_filename

        ext = Path(original_filename).suffix

        try:
            # Use first 600 chars — enough context, keeps cost low
            snippet = text.strip()[:600]

            response = self._client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": RENAME_PROMPT.format(text=snippet),
                    }
                ],
                temperature=0.2,   # low temp = consistent, predictable names
                max_tokens=30,     # filenames are short
            )

            raw = response.choices[0].message.content.strip()

            # Sanitise
            new_stem = self._sanitise(raw)

            if not new_stem:
                logger.warning("Empty rename response for '%s' — keeping original.", original_filename)
                return original_filename

            new_name = new_stem + ext
            logger.info("  ✏️  Smart Renamed: '%s' → '%s'", original_filename, new_name)
            return new_name

        except Exception as exc:
            logger.warning(
                "Smart Rename failed for '%s': %s — keeping original.",
                original_filename, exc,
            )
            return original_filename

    @staticmethod
    def _sanitise(name: str) -> str:
        """Clean AI response into a valid filename stem."""
        # Strip any extension the AI may have added
        name = Path(name).stem if "." in name else name

        # Take only the first line (sometimes AI adds explanation)
        name = name.split("\n")[0].strip()

        # Replace spaces with underscores
        name = name.replace(" ", "_")

        # Remove illegal characters — keep alphanumeric, underscores, hyphens
        name = re.sub(r"[^\w\-]", "", name)

        # Remove leading/trailing underscores
        name = name.strip("_")

        # Cap length
        return name[:80]
