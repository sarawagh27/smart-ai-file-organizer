from smart_ai_file_organizer.renamer import SmartRenamer


class FailingCompletions:
    def create(self, **_kwargs):
        raise RuntimeError("network down")


class FailingChat:
    completions = FailingCompletions()


class FailingClient:
    chat = FailingChat()


def test_sanitise_strips_extension_spaces_and_symbols():
    assert SmartRenamer._sanitise("Invoice Amazon 2026!!.pdf") == "Invoice_Amazon_2026"


def test_sanitise_uses_first_line_and_caps_length():
    raw = "A" * 100 + "\nextra"
    assert SmartRenamer._sanitise(raw) == "A" * 80


def test_rename_returns_original_when_api_fails():
    renamer = SmartRenamer(enabled=False)
    renamer.enabled = True
    renamer._client = FailingClient()

    result = renamer.rename("scan.txt", "invoice payment bank account tax revenue")

    assert result == "scan.txt"
