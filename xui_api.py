import requests
import uuid
import json
import urllib.parse
from datetime import datetime, timedelta
import config
import warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class XUIClient:
    def __init__(self):
        self.base_url = config.XUI_PANEL_URL.rstrip('/')
        self.session = requests.Session()
        self.session.verify = False  # Отключить проверку SSL
        self.cookie = None
        
    def login(self):
        """Авторизация в панели 3X-UI"""
        url = f"{self.base_url}/login"
        data = {
            'username': config.XUI_USERNAME,
            'password': config.XUI_PASSWORD
        }
        try:
            response = self.session.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.cookie = response.cookies
                    return True
            return False
        except Exception as e:
            print(f"Ошибка авторизации: {e}")
            return False
    
    def get_inbound_info(self, inbound_id):
        """Получить информацию об inbound"""
        if not self.login():
            raise Exception("Не удалось авторизоваться")
        
        url = f"{self.base_url}/panel/api/inbounds/get/{inbound_id}"
        response = self.session.get(url, cookies=self.cookie, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return result.get('obj')
        return None
    
    def create_client(self, email, days, traffic_gb, inbound_id=None, sub_id=None):
        """Создать нового клиента VPN"""
        if inbound_id is None:
            inbound_id = config.XUI_INBOUND_ID
            
        if not self.login():
            raise Exception("Не удалось авторизоваться в панели")
        
        # Получаем информацию об inbound
        inbound_info = self.get_inbound_info(inbound_id)
        if not inbound_info:
            raise Exception(f"Inbound с ID {inbound_id} не найден! Создайте inbound в панели.")
        
        # Генерация UUID для клиента
        client_uuid = str(uuid.uuid4())
        
        # Генерация subId если не передан (для subscription URL)
        if sub_id is None:
            import secrets
            sub_id = secrets.token_urlsafe(12)
        
        # Расчет времени истечения (в миллисекундах)
        expire_time = int((datetime.now() + timedelta(days=days)).timestamp() * 1000)
        
        # Трафик в байтах (GB -> bytes)
        total_traffic = traffic_gb * 1024 * 1024 * 1024
        
        url = f"{self.base_url}/panel/api/inbounds/addClient"
        
        # Получаем текущие настройки inbound
        current_settings = json.loads(inbound_info.get('settings', '{}'))
        protocol = inbound_info.get('protocol', 'vless')
        
        # Формируем данные нового клиента в зависимости от протокола
        new_client = {
            "email": email,
            "enable": True,
            "expiryTime": expire_time,
            "totalGB": total_traffic,
            "subId": sub_id,
        }
        
        # Добавляем специфичные для протокола поля
        if protocol == 'vless':
            new_client['id'] = client_uuid
            new_client['flow'] = ''
        elif protocol == 'vmess':
            new_client['id'] = client_uuid
            new_client['alterId'] = 0
        elif protocol == 'trojan':
            new_client['password'] = client_uuid  # Для trojan используется password вместо id
        else:
            # Для остальных протоколов
            new_client['id'] = client_uuid
        
        # Формируем финальный запрос
        client_data = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [new_client]
            })
        }
        
        response = self.session.post(url, json=client_data, cookies=self.cookie, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                # Формируем subscription URL
                # Берем базовый домен из panel URL
                base_domain = self.base_url.split('/')[0] + '//' + self.base_url.split('/')[2]
                config_link = f"{base_domain}/{config.SUB_PATH}/{sub_id}"
                
                return {
                    'client_id': client_uuid,
                    'email': email,
                    'sub_id': sub_id,
                    'config_link': config_link,
                    'expires_at': datetime.fromtimestamp(expire_time / 1000)
                }
            else:
                raise Exception(f"API вернул ошибку: {result.get('msg', 'Unknown error')}")
        else:
            raise Exception(f"Ошибка HTTP {response.status_code}: {response.text}")
    
    def get_client_link(self, inbound_id, email):
        """Получить subscription ссылку клиента"""
        # Для 3X-UI PRO используем subscription URL
        # Формат: https://panel-url/sub/client_uuid
        
        if not self.login():
            raise Exception("Не удалось авторизоваться")
        
        # Получаем информацию об inbound чтобы найти subId клиента
        inbound_info = self.get_inbound_info(inbound_id)
        if not inbound_info:
            return f"Ошибка: inbound {inbound_id} не найден"
        
        # Парсим настройки
        settings = json.loads(inbound_info.get('settings', '{}'))
        clients = settings.get('clients', [])
        
        # Ищем нашего клиента по email
        client = None
        for c in clients:
            if c.get('email') == email:
                client = c
                break
        
        if not client:
            return f"Ошибка: клиент {email} не найден"
        
        # Получаем subId клиента (для subscription URL)
        sub_id = client.get('subId', '')
        
        if sub_id:
            # Формируем subscription URL
            # Убираем /panel/api/... из base_url и добавляем /sub/
            base = self.base_url.rstrip('/')
            return f"{base}/sub/{sub_id}"
        else:
            # Если subId нет, возвращаем UUID/password
            protocol = inbound_info.get('protocol', 'vless')
            if protocol == 'trojan':
                return client.get('password', 'Ошибка')
            else:
                return client.get('id', 'Ошибка')
        
        # Если не получилось через API, возвращаем заглушку
        return f"Ошибка получения ссылки для {email}"
    
    def delete_client(self, inbound_id, client_uuid):
        """Удалить клиента по UUID"""
        if not self.login():
            return False
        
        url = f"{self.base_url}/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}"
        response = self.session.post(url, cookies=self.cookie, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('success', False)
        return False
    
    def delete_client_by_email(self, email, inbound_ids=None):
        """Удалить клиента по email из указанных inbounds (или из всех стандартных)"""
        if inbound_ids is None:
            inbound_ids = [config.INBOUND_XHTTP, config.INBOUND_TROJAN]
        
        if not self.login():
            return False
        
        deleted_count = 0
        for inbound_id in inbound_ids:
            try:
                # Получаем информацию об inbound
                inbound_info = self.get_inbound_info(inbound_id)
                if not inbound_info:
                    continue
                
                # Парсим настройки
                settings = json.loads(inbound_info.get('settings', '{}'))
                clients = settings.get('clients', [])
                protocol = inbound_info.get('protocol', 'vless')
                
                # Ищем клиента по email
                for client in clients:
                    if client.get('email') == email:
                        # Получаем UUID или password в зависимости от протокола
                        if protocol == 'trojan':
                            client_uuid = client.get('password')
                        else:
                            client_uuid = client.get('id')
                        
                        if client_uuid:
                            # Удаляем клиента
                            url = f"{self.base_url}/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}"
                            response = self.session.post(url, cookies=self.cookie, timeout=10)
                            if response.status_code == 200:
                                result = response.json()
                                if result.get('success'):
                                    deleted_count += 1
                        break
            except Exception as e:
                # Логируем ошибки только при необходимости
                pass
                continue
        
        return deleted_count > 0
    
    def delete_client_by_uuid(self, client_uuid, inbound_ids=None):
        """Удалить клиента по UUID из указанных inbounds (или из всех стандартных)"""
        if inbound_ids is None:
            inbound_ids = [config.INBOUND_XHTTP, config.INBOUND_TROJAN]
        
        if not self.login():
            return False
        
        deleted_count = 0
        for inbound_id in inbound_ids:
            try:
                result = self.delete_client(inbound_id, client_uuid)
                if result:
                    deleted_count += 1
            except Exception as e:
                pass
                continue
        
        return deleted_count > 0
    
    def list_inbounds(self):
        """Получить список всех inbounds"""
        if not self.login():
            return []
        
        url = f"{self.base_url}/panel/api/inbounds/list"
        response = self.session.get(url, cookies=self.cookie, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return result.get('obj', [])
        return []
