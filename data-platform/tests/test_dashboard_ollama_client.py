"""Pruebas del cliente local de Ollama usado por el dashboard."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "dashboard"))

from ollama_client import OllamaClient, OllamaClientError  # noqa: E402


class OllamaClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = OllamaClient(
            "http://ollama.test",
            model="llama3.2:1b",
            timeout=2,
        )

    @patch("ollama_client.requests.post")
    def test_sends_general_question_and_history(self, post: Mock) -> None:
        response = post.return_value
        response.status_code = 200
        response.json.return_value = {"message": {"content": "¡Hola!"}}
        history = [{"role": "user", "content": "Hola"}]

        result = self.client.ask("¿Qué puedes hacer?", history)

        self.assertEqual(result, "¡Hola!")
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["model"], "llama3.2:1b")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["messages"][-2:], history + [
            {"role": "user", "content": "¿Qué puedes hacer?"}
        ])
        post.assert_called_once_with(
            "http://ollama.test/api/chat",
            json=payload,
            timeout=2,
        )

    @patch("ollama_client.requests.post")
    def test_reports_unavailable_ollama_service(self, post: Mock) -> None:
        post.side_effect = requests.ConnectionError("offline")

        with self.assertRaisesRegex(OllamaClientError, "No se pudo conectar con Ollama"):
            self.client.ask("Hola")

    @patch("ollama_client.requests.post")
    def test_blocks_sales_questions_without_calling_ollama(self, post: Mock) -> None:
        with self.assertRaisesRegex(OllamaClientError, "Ventas verificadas"):
            self.client.ask("¿Cuánto vendimos este mes?")

        post.assert_not_called()

    @patch("ollama_client.requests.post")
    def test_suggests_pulling_missing_model(self, post: Mock) -> None:
        post.return_value.status_code = 404

        with self.assertRaisesRegex(OllamaClientError, "ollama pull llama3.2:1b"):
            self.client.ask("Hola")

    @patch("ollama_client.requests.post")
    def test_rejects_unexpected_response_shape(self, post: Mock) -> None:
        response = post.return_value
        response.status_code = 200
        response.json.return_value = {"message": {"content": ""}}

        with self.assertRaisesRegex(OllamaClientError, "formato inesperado"):
            self.client.ask("Hola")


if __name__ == "__main__":
    unittest.main()
