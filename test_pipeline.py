"""Unit tests for the extract and transform modules."""

import pytest
from unittest.mock import patch, MagicMock
from scripts.extract import fetch_astronauts
from scripts.transform import transform_astronauts


class TestExtract:

    def test_fetch_returns_valid_payload(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": "success",
            "number": 2,
            "people": [
                {"name": "Jane Doe", "craft": "ISS"},
                {"name": "John Smith", "craft": "ISS"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("scripts.extract.requests.get", return_value=mock_response):
            result = fetch_astronauts()

        assert result["message"] == "success"
        assert result["number"] == 2
        assert len(result["people"]) == 2
        assert "fetched_at" in result

    def test_fetch_raises_on_bad_message(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": "error", "people": []}
        mock_response.raise_for_status = MagicMock()

        with patch("scripts.extract.requests.get", return_value=mock_response):
            with pytest.raises(ValueError, match="Unexpected API message"):
                fetch_astronauts()

    def test_fetch_raises_on_missing_people(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": "success"}
        mock_response.raise_for_status = MagicMock()

        with patch("scripts.extract.requests.get", return_value=mock_response):
            with pytest.raises(ValueError, match="Missing or malformed"):
                fetch_astronauts()


class TestTransform:

    def _raw(self, people):
        return {
            "message": "success",
            "number": len(people),
            "people": people,
            "fetched_at": "2024-06-01T07:00:00+00:00",
        }

    def test_transform_cleans_names_and_crafts(self):
        raw = self._raw([{"name": "  jane doe  ", "craft": "iss"}])
        records = transform_astronauts(raw)

        assert len(records) == 1
        assert records[0]["name"] == "Jane Doe"
        assert records[0]["craft"] == "ISS"

    def test_transform_skips_missing_name(self):
        raw = self._raw([
            {"name": "", "craft": "ISS"},
            {"name": "Valid Person", "craft": "ISS"},
        ])
        records = transform_astronauts(raw)
        assert len(records) == 1
        assert records[0]["name"] == "Valid Person"

    def test_transform_skips_missing_craft(self):
        raw = self._raw([
            {"name": "Jane Doe", "craft": ""},
            {"name": "John Smith", "craft": "ISS"},
        ])
        records = transform_astronauts(raw)
        assert len(records) == 1
        assert records[0]["name"] == "John Smith"

    def test_transform_empty_people(self):
        raw = self._raw([])
        records = transform_astronauts(raw)
        assert records == []

    def test_transform_preserves_fetched_at(self):
        raw = self._raw([{"name": "Jane Doe", "craft": "ISS"}])
        records = transform_astronauts(raw)
        assert records[0]["fetched_at"] == "2024-06-01T07:00:00+00:00"
