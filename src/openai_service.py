"""
OpenAI service for transcription and analysis.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

from openai import OpenAI
from loguru import logger

from config import config
from models import TranscriptionResult, RoleTaggedDialogue, CallQualityScore, CallAnalysisResult, ChecklistAnalysisResult


class OpenAIService:
    """Service for OpenAI API interactions."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.openai_model
        
    async def transcribe_audio(self, audio_file_path: str) -> Optional[TranscriptionResult]:
        """Transcribe audio file using OpenAI Whisper."""
        try:
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
            
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            result = TranscriptionResult(text=transcript)
            logger.info(f"Successfully transcribed audio file: {audio_path.name}")
            logger.debug(f"Transcription length: {len(transcript)} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio file {audio_file_path}: {e}")
            return None
    
    async def tag_dialogue_roles(self, transcription_text: str) -> Optional[RoleTaggedDialogue]:
        """Tag dialogue with speaker roles using exact prompt from n8n workflow."""
        
        # Exact system prompt from the n8n workflow
        system_prompt = """# Обзор
Ты являешься супер экспертом, который специализируется на глубоком анализе записей встреч

Ты получаешь полную транскрибацию звонка в виде сплошного текста. Твоя задача — сохранить весь исходный текст, но разделить его на реплики и явно пометить, где говорит продавец, а где говорит клиент.

# Продавцы компании
Имена Продавцов: Елизавета, Владимир , Надежда

# Название компании
Весткол

# Роль
Прочитай транскрибацию и добавь перед каждой репликой соответствующую приписку:
Если говорит продавец, добавь в начале строки "Продавец:".
Если говорит клиент, добавь в начале строки "Клиент:".

Текст не сокращай, структуру не меняй, ничего не удаляй и не переписывай, только добавляй нужные приписки.

#Вывод
Вывод должен быть в таком формате через новую строчку!

Клиент:
Продавец:

# Задача

Твоя задача - корректно и четко распределить роли. Продавец как правило рассказывает про клуб, преимущества. Следи за этим перед распределением. Не должно быть такого, что текст клиента приписывается менеджеру"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcription_text}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            tagged_content = response.choices[0].message.content.strip()
            
            result = RoleTaggedDialogue(
                content=tagged_content,
                original_text=transcription_text
            )
            
            logger.info("Successfully tagged dialogue with speaker roles")
            return result
            
        except Exception as e:
            logger.error(f"Failed to tag dialogue roles: {e}")
            return None
    
    async def analyze_call_quality(self, tagged_dialogue: str) -> Optional[CallQualityScore]:
        """Analyze call quality using exact prompt and JSON schema from n8n workflow."""
        
        # Exact system prompt from the n8n workflow
        system_prompt = """# Overview
Ты — эксперт по контролю качества звонков.  
У тебя есть транскрибация звонка.  
Твоя задача:
1. Определить — звонок входящий (клиент позвонил в компанию) или исходящий (продавец звонит клиенту).  
2. Выставить оценку по каждому чеклист-пункту.  
3. Вернуть иерархический JSON в точности по структуре таблицы.  

# Rules
- Формат ответа: строго JSON-объект.  
- В ответе ДОЛЖЕН быть только один JSON-объект.  
- Никакого текста, пояснений или комментариев.  
- Для каждого чеклист-пункта укажи число:  
  - `1` — пункт выполнен явно  
  - `0.5` — выполнен частично  
  - `0` — не выполнен  
- Если информации нет — ставь `0`.  
- В каждом блоке добавляй поле `"Итого"`, где суммируешь все значения этого блока.  
- В конце добавь `"ВСЕГО"`, где сумма всех блоков.  
- Обязательно добавь поле `"Тип звонка"` со значением `"Входящий"` или `"Исходящий"`.  

# Output
Пример JSON-структуры:

{
  "Тип звонка": "Исходящий",
  "Этап ПРИВЕТСТВИЕ": {
    "Время до соединения с менеджером": 0,
    "Корпоративное приветсвие": 1,
    "Тон добродушный, приветливый, есть улыбка в голосе": 0.5,
    "Не тараторит, не съедает слова": 1,
    "Озвучивает цель звонка инфоповод": 1,
    "Не использует фразу 'вам удобно разговаривать'": 1,
    "Не использует фразу 'как к вам можно обращаться'": 1,
    "Итого": 5.5
  },
  "Этап УСТАНОВЛЕНИЕ КОНТАКТА": {
    "Обращается по имени, минимум 2 раза": 0.5,
    "Не перебивает, дослушивает до конца": 1,
    "Говорит на простом понятном языке": 1,
    "Отсутствует сухой формальный тон": 0.5,
    "Общается на 'равных'": 0.5,
    "Использует приемы Small talk": 0,
    "Говорит комплимент, похвалу": 1,
    "Использует юмор": 0,
    "Итого": 4.5
  },
  "Этап ПРОГРАММИРОВАНИЯ": {
    "Использует программирование в начале разговора": 0,
    "На протяжении всего диалога менеджер 'ведет'": 1,
    "Итого": 1
  },
  "Этап СОЗДАНИЯ ПОТРЕБНОСТИ": {
    "Задал обязательные вопросы": 0,
    "Делает презентацию компании": 0.5,
    "Не говорит 'Мы оператор/провайдер интернет услуг'": 1,
    "Выясняет чем занимается компания": 1,
    "Выясняет подключена ли услуга интернет": 0,
    "Если все устраивает, узнает про резервный канал": 0,
    "Узнает о случаях атак": 0,
    "Задает вопросы про доп. услуги": 0,
    "Итого": 2.5
  },
  "Этап ПРЕЗЕНТАЦИЯ": {
    "Делает презентацию 2-3 услуг": 0,
    "Рассказывает о кейсах или отзывах": 0,
    "Предлагает отправить КП или тестовый период": 0,
    "Менеджер знает продукт": 1,
    "Итого": 1
  },
  "Этап РАБОТА С СОМНЕНИЯМИ": {
    "Отрабатывает все возражения": 0,
    "Присоединяется при отработке возражений": 0,
    "Аргументы соответствуют возражению": 0,
    "Не спорит с клиентом": 1,
    "Предлагает отправить КП после отработки": 0,
    "Итого": 1
  },
  "ЭТАП ЗАВЕРШЕНИЯ": {
    "Уточняет остались ли вопросы": 0,
    "Уточняет куда отправить КП": 0,
    "Спросить к какой дате нужна услуга": 0,
    "Резюмировал разговор": 0,
    "Озвучивает следующие шаги": 0,
    "Оставил контакты и поблагодарил": 1,
    "Итого": 1
  },
  "ВСЕГО": 16.5
}

# Output Format
Верни только JSON в этом формате.  
Без текста, пояснений или схемы."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Текст аудио: {tagged_dialogue}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                json_data = json.loads(response_text)
                
                # Map the JSON data to our model
                quality_score = CallQualityScore(
                    **json_data,
                    detailed_scores=json_data
                )
                
                logger.info("Successfully analyzed call quality")
                return quality_score
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response text: {response_text}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to analyze call quality: {e}")
            return None
    
    async def detailed_call_analysis(self, tagged_dialogue: str) -> Optional[CallAnalysisResult]:
        """Perform detailed call analysis using the second analysis prompt."""
        
        # Second analysis prompt from the n8n workflow 
        system_prompt = """# Overview
Ты — профессиональный аналитик продаж и коммуникаций, твоя задача — по тексту диалога анализировать эффективность работы менеджера, определять этапы воронки, выявлять потребности клиента и указывать зоны роста.

Тебе надо сформировать следующие переменные. В тексте дается пример того, что надо писать. НЕ ЖАДНИЧАЙ НА ТЕКСТ. ОТВЕЧАЙ ПОДРОБНО И РАЗВЕРНУТО.

Тебе передается реальный диалог между менеджером и клиентом (текст аудио)

# Role

Твоя задача — строго по структуре output (см. ниже) заполнить все поля, даже если какие-то данные отсутствуют — в этом случае пиши "нет данных" или давай максимально вероятный ответ по контексту.

Вся логика должна быть развернута и обоснована — особенно там, где ты выставляешь проценты или даёшь субъективные оценки. Не додумывай имена и факты, если их нет в тексте, но логически интерпретируй смысл сказанного.

Перед анализом внимательно изучи структуру и описание каждого поля.

# Output 

ВОТ ПЕРЕМЕННЫЕ КОТОРЫЕ НУЖНО СФОРМИРОВАТЬ:

"summary" — Краткое резюме разговора (5–15 предложений):
Что обсудили, на чем сделали акцент, каков общий настрой клиента, какой результат по итогу встречи.

"client_talks_most" — Кто говорил больше (да/нет + краткое пояснение). Да/Нет. Объясни, почему: например, клиент активно делился опытом и вопросами или, наоборот, отвечал коротко, а инициативу держал менеджер.

client_name — Имя клиента (по возможности ФИО). Пример: Иванов Иван.

style_adaptation — Адаптация стиля менеджера под клиента (да/нет + пояснение). Да/Нет. Поясни — использовал ли менеджер лексику и темп, близкий клиенту, подстраивался ли под его энергетику. 5-8 предложений с цитатами

target_client — Целевой ли клиент для клуба. Да/Нет. Владелец агентства, есть запрос на рост и развитие.

client_needs — Основные потребности и мотивация клиента.Зачем в клуб, чего ожидает, какой результат хочет получить. 5-8 предложений с цитатами

contact_establishment.value — Оценка установления контакта (0–100).  Насколько успешно менеджер установил контакт: был ли смолток, удалось ли расположить клиента, плавность перехода к делу.

contact_establishment.explanation — Пояснение по установлению контакта. Как прошел первый этап, были ли барьеры, насколько быстро удалось перейти к сути. 5-8 предложений с цитатами
й

qualification.value — Квалификация клиента (0–100). Насколько глубоко выяснили, кто клиент, его контекст, источник знакомства с клубом, мотивацию на данном этапе.

qualification.explanation — Пояснение по квалификации. Какие вопросы были заданы, насколько полно менеджер раскрыл контекст и мотивацию клиента. 5-8 предложений с цитатами

needs_identification.value — Оценка выявления потребностей (0–100). Насколько четко и глубоко выявлены реальные потребности и цели клиента.

needs_identification.explanation — Пояснение по выявлению потребностей. Какие запросы и задачи клиента были зафиксированы, насколько полно менеджер понял ожидания. 5-8 предложений с цитатами


product_presentation.value — Оценка презентации продукта (0–100). Насколько презентация продукта была адаптирована под задачи клиента.

product_presentation.explanation — Пояснение по презентации. Какие выгоды и решения были показаны, насколько персонализированно менеджер рассказывал о клубе. 5-8 предложений с цитатами

objection_handling.value — Оценка работы с возражениями (0–100). Как менеджер работал с возражениями, насколько эффективно снял опасения клиента.

objection_handling.explanation — Пояснение по работе с возражениями. Какие вопросы или возражения звучали, как менеджер их закрыл. 5-8 предложений с цитатами

hidden_objections — Скрытые возражения, которые не были отработаны. Запиши неочевидные опасения, которые могли остаться. 5-8 предложений с цитатами


closing.value — Оценка закрытия сделки (0–100). Была ли попытка закрытия (например, предложен ван-тайм оффер), насколько корректно и уверенно.

closing.explanation — Пояснение по закрытию сделки. Что именно предложил менеджер, как отреагировал клиент, было ли согласие или нет. 5-8 предложений с цитатами

sale_probability.value — Вероятность продажи (0–100). Твоя субъективная оценка, насколько клиент готов купить.

sale_probability.explanation — Краткое объяснение вероятности продажи. Что говорит за и против, какие сигналы дал клиент. 5-8 предложений с цитатами


next_step — Следующий шаг после встречи. Что согласовали, какие действия стоит сделать менеджеру дальше, чтобы не терять динамику.

В ответ иногда включай цитаты из ответов"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Текст аудио: {tagged_dialogue}"}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse the structured response (would need custom parsing for this format)
            # For now, return a basic structure
            logger.info("Successfully performed detailed call analysis")
            logger.debug(f"Analysis result length: {len(response_text)} characters")
            
            # This would need proper parsing based on the expected output format
            # For now, return None as this is complex to implement without more specific format
            return None
            
        except Exception as e:
            logger.error(f"Failed to perform detailed call analysis: {e}")
            return None
    
    async def structured_call_analysis(self, tagged_dialogue: str) -> Optional[CallAnalysisResult]:
        """
        Perform structured call analysis using JSON output format.
        
        This implements the proper structured analysis from call_analyse_structure.
        """
        system_prompt = """# Overview
Ты — профессиональный аналитик продаж и коммуникаций, твоя задача — по тексту диалога анализировать эффективность работы менеджера, определять этапы воронки, выявлять потребности клиента и указывать зоны роста.

Тебе передается реальный диалог между менеджером и клиентом (текст аудио)

# Role
Твоя задача — строго по структуре JSON output заполнить все поля, даже если какие-то данные отсутствуют — в этом случае пиши "нет данных" или давай максимально вероятный ответ по контексту.

Вся логика должна быть развернута и обоснована — особенно там, где ты выставляешь проценты или даёшь субъективные оценки. Не додумывай имена и факты, если их нет в тексте, но логически интерпретируй смысл сказанного.

ОБЯЗАТЕЛЬНО отвечай в формате JSON со следующими полями:
- summary: краткое резюме разговора (5-15 предложений)
- client_talks_most: кто говорил больше (да/нет + пояснение)
- client_name: имя клиента
- style_adaptation: адаптация стиля менеджера (да/нет + пояснение)
- target_client: целевой ли клиент (да/нет + пояснение)
- client_needs: потребности клиента
- manager_responsible: ФИО менеджера
- contact_establishment: {value: 0-100, explanation: пояснение}
- qualification: {value: 0-100, explanation: пояснение}
- needs_identification: {value: 0-100, explanation: пояснение}
- product_presentation: {value: 0-100, explanation: пояснение}
- objection_handling: {value: 0-100, explanation: пояснение}
- closing: {value: 0-100, explanation: пояснение}
- sale_probability: {value: 0-100, explanation: пояснение}
- hidden_objections: скрытые возражения
- next_step: следующий шаг

В пояснениях используй цитаты из диалога. Отвечай ТОЛЬКО в JSON формате."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проанализируй следующий диалог:\n\n{tagged_dialogue}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=4000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response into CallAnalysisResult model
            import json
            from pydantic import ValidationError
            
            try:
                analysis_data = json.loads(response_text)
                
                # Create CallAnalysisResult from the JSON data
                result = CallAnalysisResult.model_validate(analysis_data)
                
                logger.info("Successfully performed structured call analysis")
                logger.debug(f"Analysis summary: {result.summary[:100]}...")
                
                return result
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Failed to parse structured analysis response: {e}")
                logger.debug(f"Raw response: {response_text[:500]}...")
                return None
            
        except Exception as e:
            logger.error(f"Failed to perform structured call analysis: {e}")
            return None
    
    async def checklist_analysis(self, tagged_dialogue: str) -> Optional[ChecklistAnalysisResult]:
        """
        Perform checklist-based call analysis following the Excel structure.
        
        This implements the inbound Excel analyze structure.
        """
        system_prompt = """# Overview
Ты — эксперт по контролю качества звонков.  
У тебя есть транскрибация звонка.  
Твоя задача:
1. Определить — звонок входящий (клиент позвонил в компанию) или исходящий (продавец звонит клиенту).  
2. Выставить оценку по каждому чеклист-пункту.  
3. Вернуть иерархический JSON в точности по структуре таблицы.  

# Rules
- Формат ответа: строго JSON-объект.  
- В ответе ДОЛЖЕН быть только один JSON-объект.  
- Никакого текста, пояснений или комментариев.  
- Для каждого чеклист-пункта укажи число:  
  - `1` — пункт выполнен явно  
  - `0.5` — выполнен частично  
  - `0` — не выполнен  
- Если информации нет — ставь `0`.  
- В каждом блоке добавляй поле `"Total"`, где суммируешь все значения этого блока.  
- В конце добавь `"OVERALL TOTAL"`, где сумма всех блоков.  
- Обязательно добавь поле `"Call Type"` со значением `"Входящий"` или `"Исходящий"`.

ОБЯЗАТЕЛЬНО отвечай в JSON формате со следующей ТОЧНОЙ структурой:

{
  "Call Type": "Входящий / Исходящий",
  "Stage GREETING": {
    "Time before connecting to manager": 0,
    "Corporate greeting": 0,
    "Tone friendly and cheerful, smile in voice": 0,
    "Does not rush or swallow words": 0,
    "States the purpose of the call (info reason)": 0,
    "Does not use phrase 'is it convenient to talk'": 0,
    "Does not use phrase 'how can I address you'": 0,
    "Total": 0
  },
  "Stage CONTACT ESTABLISHMENT": {
    "Addresses by name at least twice": 0,
    "Does not interrupt, listens fully": 0,
    "Speaks in simple clear language": 0,
    "Avoids dry formal tone": 0,
    "Communicates as equal": 0,
    "Uses small talk (weather, events, hobbies, travel, etc.)": 0,
    "Gives compliment or praise": 0,
    "Uses humor (joke, anecdote)": 0,
    "Total": 0
  },
  "Stage PROGRAMMING": {
    "Uses programming at start to control conversation": 0,
    "Leads conversation throughout": 0,
    "Total": 0
  },
  "Stage NEED IDENTIFICATION": {
    "Asks required questions": 0,
    "Finds out company's business area": 0,
    "Finds out employee count for services": 0,
    "Checks if company has sales department": 0,
    "Identifies IT infrastructure responsible person": 0,
    "Clarifies services to connect to internet": 0,
    "Asks about additional offices in Moscow or other cities": 0,
    "Determines if equipment is required": 0,
    "Checks if workplace wiring is needed": 0,
    "Total": 0
  },
  "Stage PRESENTATION": {
    "Presents company": 0,
    "Presents 2–3 services with benefits": 0,
    "Mentions positive cases or reviews": 0,
    "Offers to send proposal or test period": 0,
    "Manager knows product, no mistakes": 0,
    "Total": 0
  },
  "Stage HANDLING OBJECTIONS": {
    "Handles all objections fully": 0,
    "Agrees and empathizes during objection": 0,
    "Arguments match objection": 0,
    "Does not argue or violate boundaries": 0,
    "Offers to send proposal after objection": 0,
    "Total": 0
  },
  "Stage CLOSING": {
    "Asks if questions remain": 0,
    "Clarifies where to send proposal": 0,
    "Asks by what date service needed": 0,
    "Summarizes conversation": 0,
    "States next steps and deadlines": 0,
    "Leaves contacts and thanks client": 0,
    "Total": 0
  },
  "OVERALL TOTAL": 0
}

Верни только JSON в этом формате. Без текста, пояснений или схемы."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проанализируй следующий диалог по чек-листу:\n\n{tagged_dialogue}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response into ChecklistAnalysisResult model
            import json
            from pydantic import ValidationError
            
            try:
                analysis_data = json.loads(response_text)
                
                # Create ChecklistAnalysisResult from the JSON data
                result = ChecklistAnalysisResult.model_validate(analysis_data)
                
                logger.info("Successfully performed checklist call analysis")
                logger.debug(f"Checklist analysis overall total: {result.overall_total}")
                
                return result
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Failed to parse checklist analysis response: {e}")
                logger.debug(f"Raw response: {response_text[:500]}...")
                return None
            
        except Exception as e:
            logger.error(f"Failed to perform checklist call analysis: {e}")
            return None