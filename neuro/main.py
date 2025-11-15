import json
import re
import asyncio
import logging
import sys
import os
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime
import traceback

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
    def __init__(self, config_file: str = 'keywords_config.json'):
        self.config_file = config_file
        self.stop_words: Set[str] = set()
        self.low_weight: Set[str] = set()
        self.high_weight: Set[str] = set()
        self.load_config()
    
    def load_config(self) -> None:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.stop_words = set(config.get('stop_words', []))
            self.low_weight = set(config.get('low_weight_words', []))
            self.high_weight = set(config.get('high_weight_words', []))
            
            logger.info(f"Config loaded: {len(self.stop_words)} stop words, "
                       f"{len(self.low_weight)} low weight, {len(self.high_weight)} high weight")
                        
        except Exception as e:
            logger.error(f"Config load error: {e}")
            self.set_defaults()
    
    def set_defaults(self) -> None:
        self.stop_words = {
            'я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они', 'себя',
            'мой', 'твой', 'его', 'её', 'наш', 'ваш', 'их',
            'этот', 'тот', 'такой', 'какой', 'всякий', 'каждый', 'любой',
        }
        self.low_weight = {
            'инвалид', 'инвалиды', 'инвалидам', 'инвалидов', 'инвалидом', 'инвалиду',
            'льгот', 'льготы', 'льготу', 'льготе',
        }
        self.high_weight = {
            'парковка', 'парковочное', 'стоянка',
            'лекарств', 'медицинск', 'рецепт', 'протез', 'ортопед',
        }
        logger.warning("Using default keywords")

class BenefitsSearch:
    def __init__(self, data_file: str, keywords_config: KeywordsConfig):
        self.data_file = data_file
        self.keywords_config = keywords_config
        self.data = []
        self.load_data()
    
    def load_data(self) -> None:
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data_content = json.load(f)
                self.data = data_content.get('benefits_database', [])
            logger.info(f"Loaded {len(self.data)} benefits")
        except Exception as e:
            logger.error(f"Data load error: {e}")
            self.data = []
    
    def filter_query(self, words: List[str]) -> List[str]:
        filtered = []
        for word in words:
            word_lower = word.lower()
            if (word_lower not in self.keywords_config.stop_words and 
                len(word_lower) > 2 and 
                not word_lower.isdigit()):
                filtered.append(word_lower)
        return filtered
    
    def analyze_query(self, query_words: List[str]) -> Tuple[bool, bool]:
        has_high = any(any(hw_word in word for hw_word in self.keywords_config.high_weight) 
                            for word in query_words)
        
        has_low_only = (all(any(lw_word in word for lw_word in self.keywords_config.low_weight) 
                                for word in query_words) and query_words)
        
        return has_high, has_low_only
    
    def get_weight(self, word: str, has_high: bool, has_low_only: bool) -> float:
        word_lower = word.lower()
        
        for high_word in self.keywords_config.high_weight:
            if high_word in word_lower:
                return 2.0
        
        if has_high:
            if any(lw_word in word_lower for lw_word in self.keywords_config.low_weight):
                return 0.1
        
        elif has_low_only:
            if any(lw_word in word_lower for lw_word in self.keywords_config.low_weight):
                return 1.8
        
        return 1.0
    
    async def search(self, query: str, max_results: int = 10) -> Tuple[List[Dict], bool]:
        try:
            await asyncio.sleep(0.01)
            
            query_lower = query.lower().strip()
            all_words = re.findall(r'[а-яё0-9-]+', query_lower)
            query_words = self.filter_query(all_words)
            
            if not query_words:
                return [], False
            
            has_high, has_low_only = self.analyze_query(query_words)
            used_low_boost = has_low_only and not has_high
            
            scored_results = []
            
            for benefit in self.data:
                score = 0.0
                benefit_keywords = [kw.lower() for kw in benefit['keywords']]
                benefit_text = benefit['benefit'].lower()
                category = benefit['category'].lower()
                
                patterns = []
                weights = []
                
                for word in query_words:
                    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                    patterns.append(pattern)
                    weight = self.get_weight(word, has_high, has_low_only)
                    weights.append(weight)
                
                if used_low_boost:
                    score += 2.0
                
                for i, pattern in enumerate(patterns):
                    if pattern.search(category):
                        score += 4 * weights[i]
                
                keyword_matches = 0
                for keyword in benefit_keywords:
                    for i, pattern in enumerate(patterns):
                        if pattern.search(keyword):
                            keyword_matches += 6 * weights[i]
                            break
                
                score += keyword_matches
                
                text_matches = 0
                for i, pattern in enumerate(patterns):
                    if pattern.search(benefit_text):
                        text_matches += 3 * weights[i]
                
                score += text_matches
                
                if used_low_boost and category in ['медицина', 'денежные выплаты', 'жилье', 'транспорт']:
                    score += 3.0
                
                if score > 0.5:
                    scored_results.append((score, benefit))
            
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            result_count = max_results * 2 if used_low_boost else max_results
            results = [result[1] for result in scored_results[:result_count]]
            
            return results, used_low_boost
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [], False
    
    async def get_answer(self, query: str, user_id: Optional[str] = None) -> str:
        try:
            user_info = f" (user: {user_id})" if user_id else ""
            logger.info(f"Processing query: '{query}'{user_info}")
            
            if not query or len(query.strip()) < 2:
                return "Пожалуйста, введите более конкретный запрос. Например: 'льготы для инвалида 2 группы'"
            
            if len(query) > 200:
                return "Запрос слишком длинный. Пожалуйста, сформулируйте его короче."
            
            results, used_low_boost = await self.search(query, max_results=15)
            
            if not results:
                if used_low_boost:
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
            
            categories = {}
            for benefit in results:
                category = benefit['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(benefit['benefit'])
            
            sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
            
            answer = f"По вашему запросу '{query}' найдены следующие льготы:\n\n"
            
            displayed = 0
            for category, benefits in sorted_categories:
                if displayed >= 5:
                    break
                    
                answer += f"{category}:\n"
                for i, benefit in enumerate(benefits):
                    if i >= 3:
                        break
                    answer += f"   • {benefit}\n"
                answer += "\n"
                displayed += 1
            
            if used_low_boost:
                answer += "---\n"
                answer += "Внимание: запрос был недостаточно точным. "
                answer += "Для более релевантных результатов используйте конкретные слова: "
                answer += "'парковка', 'лекарства', 'проезд', 'ЖКУ', 'налоги' "
                answer += "или укажите группу инвалидности.\n"
            
            answer += "---\n"
            answer += "Информация основана на официальных документах\n"
            
            logger.info(f"Query processed '{query}'{user_info}, found {len(results)} results")
            
            return answer
            
        except Exception as e:
            logger.error(f"Critical error: {e}")
            logger.error(traceback.format_exc())
            return "Произошла техническая ошибка. Пожалуйста, попробуйте позже."

class BenefitsBot:
    def __init__(self, data_file: str, keywords_config_file: str = 'keywords_config.json'):
        self.keywords_config = KeywordsConfig(keywords_config_file)
        self.search_system = BenefitsSearch(data_file, self.keywords_config)
        self.user_sessions = {}
        logger.info("Bot initialized")
    
    async def process_message(self, message: str, user_id: str) -> str:
        try:
            if len(self.user_sessions) > 1000:
                self.cleanup_sessions()
            
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    'created': datetime.now(),
                    'request_count': 0,
                    'last_activity': datetime.now()
                }
            
            session = self.user_sessions[user_id]
            session['request_count'] += 1
            session['last_activity'] = datetime.now()
            
            if message.lower() in ['/start', 'start', 'начать']:
                return await self.get_welcome()
            
            if message.lower() in ['/help', 'help', 'помощь']:
                return await self.get_help()
            
            if message.lower() in ['/stats', 'статистика']:
                return await self.get_stats(user_id)
            
            return await self.search_system.get_answer(message, user_id)
            
        except Exception as e:
            logger.error(f"Process message error: {e}")
            logger.error(traceback.format_exc())
            return "Произошла непредвиденная ошибка. Пожалуйста, попробуйте еще раз."
    
    async def get_welcome(self) -> str:
        return """Добро пожаловать в бот поиска льгот для инвалидов!

Я помогу вам найти информацию о льготах, пособиях и других мерах поддержки.

Для точного поиска используйте конкретные слова:
• Сфера: "парковка", "лекарства", "проезд", "ЖКУ", "налоги"
• Группа: "1 группа", "2 группа", "3 группа", "ребенок-инвалид"
• Конкретный запрос: "парковка для инвалидов 2 группы"

Примеры хороших запросов:
"Какие льготы по лекарствам для инвалида 2 группы?"
"Парковка для инвалидов в Москве"
"Компенсация за ЖКУ для семей с детьми-инвалидами"

Просто напишите ваш вопрос, и я найду подходящие льготы!"""
    
    async def get_help(self) -> str:
        return """Как пользоваться ботом:

Для точного поиска используйте конкретные запросы:

• По сфере: "парковка", "лекарства", "проезд", "ЖКУ"
• По группе: "льготы для 1 группы", "инвалид 2 группы"  
• Для детей: "ребенок-инвалид", "детский сад"
• Комбинированные: "парковка для инвалидов 2 группы"

Примеры хороших запросов:
"Бесплатные лекарства для инвалидов"
"Парковка для инвалидов 1 группы" 
"Компенсация за ЖКУ для семей с детьми-инвалидами"
"Налоговые льготы для инвалидов 3 группы"

Команды:
/start - начать работу
/help - помощь  
/stats - статистика

Совет: чем конкретнее запрос, тем точнее будут результаты!"""
    
    async def get_stats(self, user_id: str) -> str:
        try:
            total_users = len(self.user_sessions)
            user_requests = self.user_sessions.get(user_id, {}).get('request_count', 0)
            total_benefits = len(self.search_system.data)
            
            return f"""Статистика:

• Всего льгот в базе: {total_benefits}
• Активных пользователей: {total_users}
• Ваших запросов: {user_requests}

База данных обновляется регулярно на основе официальных документов."""
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return "Не удалось получить статистику. Попробуйте позже."
    
    def cleanup_sessions(self):
        try:
            now = datetime.now()
            expired = []
            
            for user_id, session in self.user_sessions.items():
                if (now - session['last_activity']).total_seconds() > 86400:
                    expired.append(user_id)
            
            for user_id in expired:
                del self.user_sessions[user_id]
            
            logger.info(f"Cleaned {len(expired)} old sessions")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

_bot_instance = None

async def get_bot_instance(data_file: str = 'benefits_database.json', 
                          keywords_config_file: str = 'keywords_config.json') -> BenefitsBot:
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = BenefitsBot(data_file, keywords_config_file)
    return _bot_instance

async def process_query(query: str) -> str:
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_file = os.path.join(script_dir, 'benefits_database.json')
        keywords_config_file = os.path.join(script_dir, 'keywords_config.json')
        
        bot = await get_bot_instance(data_file, keywords_config_file)
        response = await bot.process_message(query, "go_user")
        return response
    except Exception as e:
        return f"Ошибка при обработке запроса: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = asyncio.run(process_query(query))
        print(result)
    else:
        async def demo():
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(script_dir, 'benefits_database.json')
            keywords_config_file = os.path.join(script_dir, 'keywords_config.json')
            
            bot = await get_bot_instance(data_file, keywords_config_file)
            test_queries = [
                "парковка для инвалидов",
                "льготы на лекарства",
                "инвалид 2 группы"
            ]
            for query in test_queries:
                print(f"Запрос: {query}")
                response = await bot.process_message(query, "demo_user")
                print(f"Ответ: {response}")
                print("-" * 50)
        
        asyncio.run(demo())