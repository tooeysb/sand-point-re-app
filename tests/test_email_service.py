"""
Tests for email service.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.email import EmailService


class TestEmailService:
    @patch("app.services.email.settings")
    def test_console_mode_when_no_api_key(self, mock_settings):
        """Without SendGrid key, emails log to console and return True."""
        mock_settings.sendgrid_api_key = ""
        mock_settings.sendgrid_from_email = "test@test.com"
        mock_settings.sendgrid_from_name = "Test"
        mock_settings.frontend_url = "http://localhost"
        service = EmailService()
        assert service.client is None
        result = service._send_email("user@test.com", "Subject", "<p>Hi</p>")
        assert result is True

    @patch("app.services.email.settings")
    def test_send_invite_email_console(self, mock_settings):
        mock_settings.sendgrid_api_key = ""
        mock_settings.sendgrid_from_email = "noreply@test.com"
        mock_settings.sendgrid_from_name = "App"
        mock_settings.frontend_url = "http://localhost:8000"
        mock_settings.app_name = "Test App"
        mock_settings.invite_token_expire_days = 7
        service = EmailService()
        result = service.send_invite_email("user@test.com", "tok123", "Admin")
        assert result is True

    @patch("app.services.email.settings")
    def test_send_password_reset_email_console(self, mock_settings):
        mock_settings.sendgrid_api_key = ""
        mock_settings.sendgrid_from_email = "noreply@test.com"
        mock_settings.sendgrid_from_name = "App"
        mock_settings.frontend_url = "http://localhost:8000"
        mock_settings.app_name = "Test App"
        mock_settings.password_reset_token_expire_hours = 24
        service = EmailService()
        result = service.send_password_reset_email("user@test.com", "reset-tok")
        assert result is True

    @patch("app.services.email.settings")
    def test_send_welcome_email_console(self, mock_settings):
        mock_settings.sendgrid_api_key = ""
        mock_settings.sendgrid_from_email = "noreply@test.com"
        mock_settings.sendgrid_from_name = "App"
        mock_settings.frontend_url = "http://localhost:8000"
        mock_settings.app_name = "Test App"
        service = EmailService()
        result = service.send_welcome_email("user@test.com", "Alice")
        assert result is True

    @patch("app.services.email.settings")
    def test_send_welcome_email_no_name(self, mock_settings):
        mock_settings.sendgrid_api_key = ""
        mock_settings.sendgrid_from_email = "noreply@test.com"
        mock_settings.sendgrid_from_name = "App"
        mock_settings.frontend_url = "http://localhost:8000"
        mock_settings.app_name = "Test App"
        service = EmailService()
        result = service.send_welcome_email("user@test.com")
        assert result is True
