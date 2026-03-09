#test payments
# Пример тестового режима для платежной системы
class TestPaymentProcessor:
    def process_test_payment(self, amount, user_id):
        """Тестовый режим обработки платежей"""
        print(f"ТЕСТ: Обработка платежа на сумму {amount} для пользователя {user_id}")
        print("ТЕСТ: Платеж успешно обработан (тестовый режим)")
        return {
            'status': 'success',
            'transaction_id': 'test_' + str(hash(f"{user_id}{amount}")),
            'amount': amount,
            'test_mode': True
        }