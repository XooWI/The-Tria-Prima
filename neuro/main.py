import json
import re
import asyncio
import logging
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('benefits_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KeywordsConfig:
    """Класс для загрузки конфигурации ключевых слов"""
    
    def __init__(self, config_file: str = 'keywords_config.json'):
        self.config_file = config_file
        self.stop_words: Set[str] = set()
        self.low_weight_words: Set[str] = set()
        self.high_weight_words: Set[str] = set()
        self._load_config()
    
    def _load_config(self) -> None:
        """Загрузка конфигурации ключевых слов"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.stop_words = set(config.get('stop_words', []))
            self.low_weight_words = set(config.get('low_weight_words', []))
            self.high_weight_words = set(config.get('high_weight_words', []))
            
            logger.info(f"Успешно загружена конфигурация ключевых слов: {len(self.stop_words)} стоп-слов, "
                       f"{len(self.low_weight_words)} низковесных, {len(self.high_weight_words)} высоковесных")
                        
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации ключевых слов: {e}")
            # Значения по умолчанию на случай ошибки
            self._set_defaults()
    
    def _set_defaults(self) -> None:
        """Установка значений по умолчанию при ошибке загрузки"""
        self.stop_words = {
            'я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они', 'себя',
            'мой', 'твой', 'его', 'её', 'наш', 'ваш', 'их',
            'этот', 'тот', 'такой', 'какой', 'всякий', 'каждый', 'любой',
        }
        self.low_weight_words = {
            'инвалид', 'инвалиды', 'инвалидам', 'инвалидов', 'инвалидом', 'инвалиду',
            'льгот', 'льготы', 'льготу', 'льготе',
        }
        self.high_weight_words = {
            'парковка', 'парковочное', 'стоянка',
            'лекарств', 'медицинск', 'рецепт', 'протез', 'ортопед',
        }
        logger.warning("Используются ключевые слова по умолчанию")

class DisabilityBenefitsSearch:
    def __init__(self, data_file: str, keywords_config: KeywordsConfig):
        self.data_file = data_file
        self.keywords_config = keywords_config
        self.data = []
        self._load_data()
    
    def _load_data(self) -> None:
        """Загрузка данных с обработкой ошибок"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data_content = json.load(f)
                self.data = data_content.get('benefits_database', [])
            logger.info(f"Успешно загружено {len(self.data)} льгот")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")
            self.data = []
    
    def _filter_query_words(self, words: List[str]) -> List[str]:
        """Фильтрует стоп-слова из запроса"""
        filtered_words = []
        for word in words:
            word_lower = word.lower()
            # Исключаем стоп-слова и слишком короткие слова (1-2 символа)
            if (word_lower not in self.keywords_config.stop_words and 
                len(word_lower) > 2 and 
                not word_lower.isdigit()):
                filtered_words.append(word_lower)
        return filtered_words
    
    def _analyze_query(self, query_words: List[str]) -> Tuple[bool, bool]:
        """Анализирует запрос и определяет его тип"""
        has_high_weight = any(any(hw_word in word for hw_word in self.keywords_config.high_weight_words) 
                            for word in query_words)
        
        has_low_weight_only = (all(any(lw_word in word for lw_word in self.keywords_config.low_weight_words) 
                                for word in query_words) and query_words)
        
        return has_high_weight, has_low_weight_only
    
    def _get_word_weight(self, word: str, has_high_weight: bool, has_low_weight_only: bool) -> float:
        """Определяет вес слова с учетом типа запроса"""
        word_lower = word.lower()
        
        # Высокий вес для специфичных терминов
        for high_weight_word in self.keywords_config.high_weight_words:
            if high_weight_word in word_lower:
                return 2.0
        
        # Если в запросе есть высоковесные слова, низковесные слова получают очень низкий вес
        if has_high_weight:
            if any(lw_word in word_lower for lw_word in self.keywords_config.low_weight_words):
                return 0.1
        
        # Если в запросе только низковесные слова, временно повышаем их вес
        elif has_low_weight_only:
            if any(lw_word in word_lower for lw_word in self.keywords_config.low_weight_words):
                return 1.8
        
        return 1.0
    
    async def search(self, query: str, max_results: int = 10) -> Tuple[List[Dict], bool]:
        """Асинхронный поиск льгот с адаптивной системой весов"""
        try:
            await asyncio.sleep(0.01)
            
            query_lower = query.lower().strip()
            # Извлекаем все слова и фильтруем стоп-слова
            all_words = re.findall(r'[а-яё0-9-]+', query_lower)
            query_words = self._filter_query_words(all_words)
            
            if not query_words:
                return [], False
            
            # Анализируем тип запроса
            has_high_weight, has_low_weight_only = self._analyze_query(query_words)
            used_low_weight_boost = has_low_weight_only and not has_high_weight
            
            scored_results = []
            
            for benefit in self.data:
                score = 0.0
                benefit_keywords = [kw.lower() for kw in benefit['keywords']]
                benefit_text_lower = benefit['benefit'].lower()
                category_lower = benefit['category'].lower()
                
                word_patterns = []
                word_weights = []
                
                for word in query_words:
                    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                    word_patterns.append(pattern)
                    weight = self._get_word_weight(word, has_high_weight, has_low_weight_only)
                    word_weights.append(weight)
                
                # БОНУС: для запросов с низковесными словами даем базовые баллы
                if used_low_weight_boost:
                    score += 2.0
                
                # Совпадение с категорией
                for i, pattern in enumerate(word_patterns):
                    if pattern.search(category_lower):
                        score += 4 * word_weights[i]
                
                # Совпадение с ключевыми словами
                keyword_matches = 0
                for keyword in benefit_keywords:
                    for i, pattern in enumerate(word_patterns):
                        if pattern.search(keyword):
                            keyword_matches += 6 * word_weights[i]
                            break
                
                score += keyword_matches
                
                # Совпадение с текстом льготы
                text_matches = 0
                for i, pattern in enumerate(word_patterns):
                    if pattern.search(benefit_text_lower):
                        text_matches += 3 * word_weights[i]
                
                score += text_matches
                
                # Дополнительный бонус для популярных категорий при общих запросах
                if used_low_weight_boost and category_lower in ['медицина', 'денежные выплаты', 'жилье', 'транспорт']:
                    score += 3.0
                
                if score > 0.5:
                    scored_results.append((score, benefit))
            
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # Для общих запросов возвращаем больше результатов
            result_count = max_results * 2 if used_low_weight_boost else max_results
            results = [result[1] for result in scored_results[:result_count]]
            
            return results, used_low_weight_boost
            
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return [], False
    
    async def get_answer(self, query: str, user_id: Optional[str] = None) -> str:
        """Асинхронное получение ответа для пользователя"""
        try:
            user_info = f" (пользователь: {user_id})" if user_id else ""
            logger.info(f"Обработка запроса: '{query}'{user_info}")
            
            if not query or len(query.strip()) < 2:
                return "Пожалуйста, введите более конкретный запрос. Например: 'льготы для инвалида 2 группы'"
            
            if len(query) > 200:
                return "Запрос слишком длинный. Пожалуйста, сформулируйте его короче."
            
            results, used_low_weight_boost = await self.search(query, max_results=15)
            
            if not results:
                # Для совсем пустых результатов пробуем найти что-то общее
                if used_low_weight_boost:
                    # Возвращаем самые популярные льготы
                    popular_categories = ['Медицина', 'Денежные выплаты', 'ЖКУ', 'Транспорт', 'Образование']
                    popular_benefits = []
                    for benefit in self.data:
                        if benefit['category'] in popular_categories and len(popular_benefits) < 8:
                            popular_benefits.append(benefit)
                    
                    if popular_benefits:
                        results = popular_benefits
                
                if not results:
                    suggestions = [
                        "попробуйте уточнить запрос, например: 'парковка для инвалидов 2 группы'",
                        "используйте конкретные слова: 'лекарства', 'проезд', 'ЖКУ', 'образование'",
                        "укажите группу инвалидности: '1 группа', '2 группа', '3 группа'",
                        "укажите конкретную сферу: 'налоговые льготы', 'транспортные льготы', 'жилищные льготы'"
                    ]
                    suggestion = "\n• ".join(suggestions)
                    return f"По запросу '{query}' льготы не найдены.\n\nПопробуйте:\n• {suggestion}"
            
            # Группируем по категориям и сортируем категории по релевантности
            categories = {}
            for benefit in results:
                category = benefit['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(benefit['benefit'])
            
            # Сортируем категории по количеству найденных льгот (самые релевантные первыми)
            sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
            
            answer = f"🔍 По вашему запросу '{query}' найдены следующие льготы:\n\n"
            
            # Ограничиваем количество категорий для вывода
            displayed_categories = 0
            for category, benefits in sorted_categories:
                if displayed_categories >= 5:
                    break
                    
                answer += f"📋 **{category}**:\n"
                for i, benefit in enumerate(benefits):
                    if i >= 3:
                        break
                    answer += f"   • {benefit}\n"
                answer += "\n"
                displayed_categories += 1
            
            # Добавляем предупреждение, если использовалось временное повышение веса
            if used_low_weight_boost:
                answer += "---\n"
                answer += "⚠️ **Внимание:** запрос был недостаточно точным. "
                answer += "Для более релевантных результатов используйте конкретные слова: "
                answer += "'парковка', 'лекарства', 'проезд', 'ЖКУ', 'налоги' "
                answer += "или укажите группу инвалидности.\n"
            
            # Добавляем информацию об источнике
            answer += "---\n"
            answer += "💡 *Информация основана на официальных документах*\n"
            
            logger.info(f"Успешно обработан запрос '{query}'{user_info}, найдено {len(results)} результатов")
            
            return answer
            
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке запроса: {e}")
            logger.error(traceback.format_exc())
            return "Произошла техническая ошибка. Пожалуйста, попробуйте позже или обратитесь в техническую поддержку."

class BenefitsBot:
    def __init__(self, data_file: str, keywords_config_file: str = 'keywords_config.json'):
        self.keywords_config = KeywordsConfig(keywords_config_file)
        self.search_system = DisabilityBenefitsSearch(data_file, self.keywords_config)
        self.user_sessions = {}
        logger.info("Бот инициализирован")
    
    async def process_message(self, message: str, user_id: str) -> str:
        """Основной метод обработки сообщений от пользователя"""
        try:
            # Очистка старых сессий
            if len(self.user_sessions) > 1000:
                self._cleanup_sessions()
            
            # Обновление сессии пользователя
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    'created': datetime.now(),
                    'request_count': 0,
                    'last_activity': datetime.now()
                }
            
            session = self.user_sessions[user_id]
            session['request_count'] += 1
            session['last_activity'] = datetime.now()
            
            # Обработка специальных команд
            if message.lower() in ['/start', 'start', 'начать']:
                return await self._get_welcome_message()
            
            if message.lower() in ['/help', 'help', 'помощь']:
                return await self._get_help_message()
            
            if message.lower() in ['/stats', 'статистика']:
                return await self._get_stats_message(user_id)
            
            # Основной поиск
            return await self.search_system.get_answer(message, user_id)
            
        except Exception as e:
            logger.error(f"Ошибка в process_message: {e}")
            logger.error(traceback.format_exc())
            return "Произошла непредвиденная ошибка. Пожалуйста, попробуйте еще раз."
    
    async def _get_welcome_message(self) -> str:
        """Приветственное сообщение"""
        return """👋 Добро пожаловать в бот поиска льгот для инвалидов!

Я помогу вам найти информацию о льготах, пособиях и других мерах поддержки.

🎯 *Для точного поиска используйте конкретные слова:*
• *Сфера:* "парковка", "лекарства", "проезд", "ЖКУ", "налоги"
• *Группа:* "1 группа", "2 группа", "3 группа", "ребенок-инвалид"
• *Конкретный запрос:* "парковка для инвалидов 2 группы"

💡 *Примеры хороших запросов:*
"Какие льготы по лекарствам для инвалида 2 группы?"
"Парковка для инвалидов в Москве"
"Компенсация за ЖКУ для семей с детьми-инвалидами"

📝 Просто напишите ваш вопрос, и я найду подходящие льготы!"""
    
    async def _get_help_message(self) -> str:
        """Сообщение помощи"""
        return """❓ *Как пользоваться ботом:*

Для точного поиска используйте конкретные запросы:

• *По сфере:* "парковка", "лекарства", "проезд", "ЖКУ"
• *По группе:* "льготы для 1 группы", "инвалид 2 группы"  
• *Для детей:* "ребенок-инвалид", "детский сад"
• *Комбинированные:* "парковка для инвалидов 2 группы"

*Примеры хороших запросов:*
"Бесплатные лекарства для инвалидов"
"Парковка для инвалидов 1 группы" 
"Компенсация за ЖКУ для семей с детьми-инвалидами"
"Налоговые льготы для инвалидов 3 группы"

📊 *Команды:*
/start - начать работу
/help - помощь  
/stats - статистика

💡 *Совет:* чем конкретнее запрос, тем точнее будут результаты!"""
    
    async def _get_stats_message(self, user_id: str) -> str:
        """Статистика использования"""
        try:
            total_users = len(self.user_sessions)
            user_requests = self.user_sessions.get(user_id, {}).get('request_count', 0)
            total_benefits = len(self.search_system.data)
            
            return f"""📊 *Статистика:*

• Всего льгот в базе: {total_benefits}
• Активных пользователей: {total_users}
• Ваших запросов: {user_requests}

💾 База данных обновляется регулярно на основе официальных документов."""
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return "Не удалось получить статистику. Попробуйте позже."
    
    def _cleanup_sessions(self):
        """Очистка старых сессий (старше 24 часов)"""
        try:
            now = datetime.now()
            expired_users = []
            
            for user_id, session in self.user_sessions.items():
                if (now - session['last_activity']).total_seconds() > 86400:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del self.user_sessions[user_id]
            
            logger.info(f"Очищено {len(expired_users)} устаревших сессий")
        except Exception as e:
            logger.error(f"Ошибка при очистке сессий: {e}")

# Глобальный экземпляр бота
_bot_instance = None

async def get_bot_instance(data_file: str = 'benefits_database.json', 
                          keywords_config_file: str = 'keywords_config.json') -> BenefitsBot:
    """Фабрика для получения экземпляра бота (синглтон)"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = BenefitsBot(data_file, keywords_config_file)
    return _bot_instance

# Демонстрация работы улучшенной системы
async def main_demo():
    """Демонстрация работы улучшенного бота"""
    bot = await get_bot_instance('benefits_database.json', 'keywords_config.json')
    
    # Тестовые запросы для демонстрации разных сценариев
    test_scenarios = [
        ("Я инвалид, мне 16 лет, какие льготы мне положены?", "Общий запрос с фильтрацией стоп-слов"),
        ("инвалид 2 группы", "Запрос с указанием группы"),
        ("парковка для инвалидов", "Точный запрос с высоковесным словом"),
        ("лекарства для инвалидов", "Запрос с высоковесным словом"),
        ("проезд в транспорте", "Запрос с высоковесным словом")
    ]
    
    for query, description in test_scenarios:
        print(f"\n{'='*60}")
        print(f"📝 Запрос: {query}")
        print(f"📋 Тип: {description}")
        print(f"{'='*60}")
        
        response = await bot.process_message(query, "demo_user")
        print(f"🤖 Ответ:\n{response}")
        
        # Небольшая задержка между запросами
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    # Запуск демо
    try:
        asyncio.run(main_demo())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        print("Произошла критическая ошибка. Подробности в логе.")