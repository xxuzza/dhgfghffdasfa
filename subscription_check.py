# -*- coding: utf-8 -*-
"""
Модуль проверки подписки на канал
Работает с python-telegram-bot
"""
import logging
import config

logger = logging.getLogger(__name__)

async def check_user_subscription(user_id, bot_instance):
    """
    Проверка подписки пользователя на канал
    
    Args:
        user_id: ID пользователя Telegram
        bot_instance: Экземпляр бота
        
    Returns:
        True если подписан, False если нет
    """
    if not config.REQUIRED_CHANNEL_ID:
        logger.warning("REQUIRED_CHANNEL_ID not set")
        return True
    
    try:
        # Получаем статус пользователя в канале
        user_channel_status = await bot_instance.get_chat_member(
            chat_id=config.REQUIRED_CHANNEL_ID,
            user_id=user_id
        )
        
        # Проверяем статус (как в инструкции aiogram)
        # status может быть: 'creator', 'administrator', 'member', 'restricted', 'left', 'kicked'
        if user_channel_status.status != 'left':
            logger.info(f"User {user_id} is subscribed (status: {user_channel_status.status})")
            return True
        else:
            logger.info(f"User {user_id} is NOT subscribed (status: left)")
            return False
            
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False
