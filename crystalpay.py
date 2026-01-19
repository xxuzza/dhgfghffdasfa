import httpx
import hashlib
import secrets
from typing import Optional

class CrystalPayAPI:
    def __init__(self, name: str, secret1: str, secret2: str):
        self.name = name
        self.secret1 = secret1  # Secret key 1
        self.secret2 = secret2  # Secret key 2 (salt)
        self.base_url = "https://api.crystalpay.io/v2"
    
    def _generate_signature(self, *args) -> str:
        """Генерация подписи для запроса"""
        string = ':'.join(str(arg) for arg in args) + self.secret2
        return hashlib.sha1(string.encode()).hexdigest()
    
    async def create_payment(self, amount: float, order_id: str, description: str = "", lifetime: int = 30, required_method: str = None) -> Optional[dict]:
        """Создание платежа"""
        # Подпись: amount:order_id:secret2
        signature = self._generate_signature(amount, order_id)
        
        data = {
            'auth_login': self.name,
            'auth_secret': self.secret1,
            'amount': str(amount),
            'order_id': order_id,
            'type': 'purchase',
            'lifetime': lifetime,
            'signature': signature
        }
        
        if description:
            data['description'] = description
        
        if required_method:
            data['required_method'] = required_method
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/invoice/create/",
                    json=data,
                    timeout=30
                )
                result = response.json()
                
                print(f"CrystalPay create response: {result}")
                
                if result.get('error'):
                    print(f"CrystalPay error: {result}")
                    return None
                
                return result
        except Exception as e:
            print(f"CrystalPay request error: {e}")
            return None
    
    async def check_payment(self, payment_id: str) -> Optional[dict]:
        """Проверка статуса платежа"""
        # Подпись: id:secret2
        signature = self._generate_signature(payment_id)
        
        data = {
            'auth_login': self.name,
            'auth_secret': self.secret1,
            'id': payment_id,
            'signature': signature
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/invoice/info/",
                    json=data,
                    timeout=30
                )
                result = response.json()
                
                if result.get('error'):
                    return None
                
                return result
        except Exception as e:
            print(f"CrystalPay check error: {e}")
            return None
    
    async def get_balance(self) -> Optional[dict]:
        """Получение баланса"""
        # Подпись: secret2
        signature = hashlib.sha1(self.secret2.encode()).hexdigest()
        
        data = {
            'auth_login': self.name,
            'auth_secret': self.secret1,
            'signature': signature
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/balance/info/",
                    json=data,
                    timeout=30
                )
                result = response.json()
                
                if result.get('error'):
                    return None
                
                return result
        except Exception as e:
            print(f"CrystalPay balance error: {e}")
            return None
