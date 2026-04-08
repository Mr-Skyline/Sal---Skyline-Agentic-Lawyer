"""Tests for src.sal.draft — pure MIME building and label helpers (mocked Gmail)."""
from __future__ import annotations

import os
import tempfile
from email import message_from_string
from unittest.mock import MagicMock

from src.sal.draft import build_raw_mime, ensure_label_id

# ---------- build_raw_mime ----------

class TestBuildRawMime:
    def test_basic_draft(self):
        raw = build_raw_mime("Hello body", "Re: Test", "", "")
        msg = message_from_string(raw)
        assert msg["Subject"] == "Re: Test"
        payload = msg.get_payload()
        if isinstance(payload, list):
            body_text = payload[0].get_payload(decode=True).decode()
        else:
            body_text = msg.get_payload(decode=True).decode()
        assert "Hello body" in body_text

    def test_reply_headers(self):
        raw = build_raw_mime(
            "Body", "Subject", "in-reply@example.com", "ref1 ref2"
        )
        msg = message_from_string(raw)
        assert msg["In-Reply-To"] == "in-reply@example.com"
        assert msg["References"] == "ref1 ref2"
        assert msg["Subject"] == "Subject"

    def test_no_reply_headers_when_empty(self):
        raw = build_raw_mime("Body", "Subject", "", "")
        msg = message_from_string(raw)
        assert msg["In-Reply-To"] is None
        assert msg["References"] is None

    def test_with_attachment(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w"
        ) as f:
            f.write("attachment content")
            f.flush()
            path = f.name
        try:
            raw = build_raw_mime(
                "Body with attachment", "Subject", "", "", attachment_paths=[path]
            )
            msg = message_from_string(raw)
            assert msg.get_content_type() == "multipart/mixed"
            parts = msg.get_payload()
            filenames = []
            for part in parts:
                cd = part.get("Content-Disposition", "")
                if "attachment" in cd:
                    filenames.append(part.get_filename())
            assert os.path.basename(path) in filenames
        finally:
            os.unlink(path)

    def test_nonexistent_attachment_skipped(self):
        raw = build_raw_mime(
            "Body", "Subj", "", "",
            attachment_paths=["/tmp/this_file_does_not_exist_xyz.bin"],
        )
        msg = message_from_string(raw)
        assert msg.get_content_type() == "multipart/mixed"
        parts = msg.get_payload()
        attachment_parts = [
            p for p in parts
            if "attachment" in (p.get("Content-Disposition") or "")
        ]
        assert len(attachment_parts) == 0

    def test_image_attachment(self):
        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False, mode="wb"
        ) as f:
            f.write(b"\x89PNG\r\n\x1a\n fake")
            f.flush()
            path = f.name
        try:
            raw = build_raw_mime("Body", "Subj", "", "", attachment_paths=[path])
            assert "image/png" in raw or "image" in raw.lower()
        finally:
            os.unlink(path)


# ---------- ensure_label_id ----------

class TestEnsureLabelId:
    def _mock_service(self, existing_labels):
        service = MagicMock()
        list_req = MagicMock()
        list_req.execute.return_value = {"labels": existing_labels}
        service.users.return_value.labels.return_value.list.return_value = list_req
        create_req = MagicMock()
        create_req.execute.return_value = {"id": "new_label_id_99"}
        service.users.return_value.labels.return_value.create.return_value = create_req
        return service

    def test_existing_label_returned(self):
        service = self._mock_service([
            {"name": "Dispute Draft", "id": "Label_42"},
            {"name": "Other", "id": "Label_7"},
        ])
        result = ensure_label_id(service, "Dispute Draft")
        assert result == "Label_42"
        service.users.return_value.labels.return_value.create.return_value.execute.assert_not_called()

    def test_label_created_when_missing(self):
        service = self._mock_service([
            {"name": "Inbox", "id": "INBOX"},
        ])
        result = ensure_label_id(service, "Dispute Draft")
        assert result == "new_label_id_99"
        service.users.return_value.labels.return_value.create.assert_called_once()
