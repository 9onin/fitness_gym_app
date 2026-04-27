from datetime import datetime
import hashlib


class PaymentValidationError(ValueError):
    pass


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
