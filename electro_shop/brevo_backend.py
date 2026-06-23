"""
Custom Brevo Email Backend menggunakan Brevo HTTP API.
Tidak memerlukan django-anymail atau library tambahan apapun.
Menggunakan urllib bawaan Python — dijamin jalan di Vercel.
"""
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'


class BrevoEmailBackend(BaseEmailBackend):
    """
    Email backend that sends emails via Brevo's HTTP API.
    Requires BREVO_API_KEY in Django settings or environment.
    """

    def __init__(self, api_key=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = api_key or getattr(settings, 'BREVO_API_KEY', '')

    def send_messages(self, email_messages):
        if not self.api_key:
            logger.error('[BrevoBackend] BREVO_API_KEY is not set.')
            if not self.fail_silently:
                raise Exception('BREVO_API_KEY is not configured.')
            return 0

        sent_count = 0
        for message in email_messages:
            try:
                if self._send_one(message):
                    sent_count += 1
            except Exception as e:
                logger.error(f'[BrevoBackend] Failed to send email: {e}')
                if not self.fail_silently:
                    raise
        return sent_count

    def _send_one(self, message):
        # Build recipient list
        to_list = [{'email': addr} for addr in message.to]

        # Parse sender
        from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
        if '<' in from_email and '>' in from_email:
            name_part = from_email.split('<')[0].strip()
            email_part = from_email.split('<')[1].replace('>', '').strip()
            sender = {'name': name_part, 'email': email_part}
        else:
            sender = {'email': from_email}

        # Build payload
        payload = {
            'sender': sender,
            'to': to_list,
            'subject': message.subject,
        }

        # Check for HTML content
        html_content = None
        if hasattr(message, 'alternatives'):
            for content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    html_content = content
                    break

        if html_content:
            payload['htmlContent'] = html_content
        else:
            payload['textContent'] = message.body

        # Send via Brevo API
        data = json.dumps(payload).encode('utf-8')
        req = Request(BREVO_API_URL, data=data, method='POST')
        req.add_header('accept', 'application/json')
        req.add_header('content-type', 'application/json')
        req.add_header('api-key', self.api_key)

        try:
            response = urlopen(req, timeout=15)
            result = json.loads(response.read().decode('utf-8'))
            logger.info(f'[BrevoBackend] Email sent successfully: {result}')
            return True
        except HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            logger.error(f'[BrevoBackend] HTTP {e.code}: {error_body}')
            if not self.fail_silently:
                raise Exception(f'Brevo API error {e.code}: {error_body}')
            return False
        except URLError as e:
            logger.error(f'[BrevoBackend] URL Error: {e.reason}')
            if not self.fail_silently:
                raise
            return False
