from types import SimpleNamespace

from app import ask


def test_ask_prints_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(
        usage_metadata=SimpleNamespace(
            prompt_token_count=12,
            candidates_token_count=34,
        ),
        text="answer",
    )
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask.genai,
        "Client",
        lambda api_key: SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda model, contents: response
            )
        ),
    )

    assert ask.ask("question") == "answer"
    assert capsys.readouterr().out == "[usage] input_tokens=12, output_tokens=34\n"


def test_ask_reports_unavailable_token_counts(monkeypatch, capsys):
    response = SimpleNamespace(usage_metadata=None, text="answer")
    monkeypatch.setattr(ask, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        ask.genai,
        "Client",
        lambda api_key: SimpleNamespace(
            models=SimpleNamespace(
                generate_content=lambda model, contents: response
            )
        ),
    )

    assert ask.ask("question") == "answer"
    assert capsys.readouterr().out == "[usage] token counts unavailable\n"
