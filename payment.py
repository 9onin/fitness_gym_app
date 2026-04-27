from datetime import datetime
import hashlib


class PaymentValidationError(ValueError):
    pass


def parse_payment_info(payment_info):
    if not payment_info:
        return None

    raw_parts = [part.strip() for part in payment_info.split(';') if part.strip()]
    if not raw_parts:
        return None

    details = {
        'provider': 'Онлайн-оплата',
        'transaction_id': '—',
        'amount': None,
        'currency': 'RUB',
        'card_mask': '—',
        'processed_at': None,
        'status': 'Оплачено',
        'is_test': False,
    }

    first_part = raw_parts[0]
    if ':' in first_part:
        provider_code, transaction_id = first_part.split(':', 1)
        details['provider'] = 'Тестовая онлайн-оплата' if provider_code == 'online-test' else provider_code
        details['transaction_id'] = transaction_id or '—'
        details['is_test'] = provider_code == 'online-test'
    else:
        details['transaction_id'] = first_part

    for part in raw_parts[1:]:
        if '=' not in part:
            continue
        key, value = part.split('=', 1)
        key = key.strip()
        value = value.strip()

        if key == 'amount':
            try:
                details['amount'] = int(value)
            except ValueError:
                details['amount'] = None
        elif key == 'card':
            details['card_mask'] = value or '—'
        elif key == 'processed_at':
            try:
                details['processed_at'] = datetime.fromisoformat(value)
            except ValueError:
                details['processed_at'] = None
        elif key == 'currency':
            details['currency'] = value or 'RUB'

    return details


class TestPaymentProcessor:
    def process_test_payment(self, amount, user_id, card_number, cardholder_name, expiry_month, expiry_year, cvv):
        normalized_number = self._normalize_card_number(card_number)

        if not self._passes_luhn(normalized_number):
            raise PaymentValidationError('Введите корректный номер карты')

        if not cardholder_name.strip():
            raise PaymentValidationError('Укажите имя владельца карты')

        if not self._is_card_active(expiry_month, expiry_year):
            raise PaymentValidationError('Срок действия карты истек')

        if not cvv.isdigit() or len(cvv) not in (3, 4):
            raise PaymentValidationError('Введите корректный CVV/CVC код')

        transaction_seed = f'{user_id}:{amount}:{normalized_number[-4:]}:{datetime.utcnow().isoformat()}'
        transaction_id = 'test_' + hashlib.sha256(transaction_seed.encode('utf-8')).hexdigest()[:16]

        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'amount': amount,
            'currency': 'RUB',
            'card_last4': normalized_number[-4:],
            'cardholder_name': cardholder_name.strip(),
            'processed_at': datetime.utcnow().isoformat(timespec='seconds'),
            'test_mode': True
        }

    def _normalize_card_number(self, card_number):
        digits_only = ''.join(ch for ch in card_number if ch.isdigit())
        if len(digits_only) < 13 or len(digits_only) > 19:
            raise PaymentValidationError('Введите корректный номер карты')
        return digits_only

    def _passes_luhn(self, card_number):
        checksum = 0
        for index, char in enumerate(card_number[::-1]):
            digit = int(char)
            if index % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

    def _is_card_active(self, expiry_month, expiry_year):
        try:
            month = int(expiry_month)
            year = int(expiry_year)
        except (TypeError, ValueError):
            raise PaymentValidationError('Укажите срок действия карты')

        if month < 1 or month > 12:
            raise PaymentValidationError('Укажите корректный месяц действия карты')

        current = datetime.utcnow()
        if year < current.year:
            return False
        if year == current.year and month < current.month:
            return False
        return True
