from __future__ import annotations

import pytest

from ai_assistants.nlg.rewriter import maybe_rewrite


class FakeRewriter:
    def rewrite(self, *, user_text: str, draft_text: str, domain: str) -> str:
        return f"[{domain}] {draft_text} (reworded)"


class BadRewriterDropsId:
    def rewrite(self, *, user_text: str, draft_text: str, domain: str) -> str:
        return "No hay info disponible."


class BadRewriterAddsId:
    def rewrite(self, *, user_text: str, draft_text: str, domain: str) -> str:
        return f"{draft_text}\nOrden ORDER-999."


class GoodRewriterKeepsIds:
    def rewrite(self, *, user_text: str, draft_text: str, domain: str) -> str:
        return draft_text.replace("estado=", "estado: ")


def test_nlg_disabled_returns_draft() -> None:
    out = maybe_rewrite(rewriter=None, user_text="hola", draft_text="draft", domain="purchases")
    assert out == "draft"


def test_nlg_enabled_uses_rewriter() -> None:
    out = maybe_rewrite(rewriter=FakeRewriter(), user_text="hola", draft_text="draft", domain="purchases")
    assert out == "[purchases] draft (reworded)"


def test_nlg_strict_rejects_dropped_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_LLM_NLG_STRICT", "1")
    draft = "Orden ORDER-200: estado=shipped, creada=2025-02-10T16:30:00+00:00."
    out = maybe_rewrite(rewriter=BadRewriterDropsId(), user_text="x", draft_text=draft, domain="purchases")
    assert out == draft


def test_nlg_strict_rejects_added_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_LLM_NLG_STRICT", "1")
    draft = "Tracking TRACK-9002: estado=in_transit, última actualización=2025-02-12T09:00:00+00:00."
    out = maybe_rewrite(rewriter=BadRewriterAddsId(), user_text="x", draft_text=draft, domain="purchases")
    assert out == draft


def test_nlg_strict_allows_safe_rewrite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_LLM_NLG_STRICT", "1")
    draft = "Orden ORDER-200: estado=shipped, creada=2025-02-10T16:30:00+00:00."
    out = maybe_rewrite(rewriter=GoodRewriterKeepsIds(), user_text="x", draft_text=draft, domain="purchases")
    assert out != draft


