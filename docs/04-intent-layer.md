# Intent Layer

## Назначение

Превратить фразу пользователя на естественном языке
в формализованный Goal Object.

## Пример

Пользователь: "Хочу повысить продукцию белка X в CHO,
не меняя сам ген."

Goal Object:

{
  "intent": "increase_expression",
  "target": {
    "gene": "X",
    "organism": "Cricetulus griseus",
    "cell_line": "CHO-K1"
  },
  "constraints": ["do_not_modify_CDS"],
  "phenotype_target": {
    "metric": "protein_yield",
    "direction": "up"
  }
}

## Компоненты

### Parser
- LLM (Claude/GPT/локальная) + RAG по BioKG
- Извлекает: организм, ген, цель, ограничения
- Нормализует через онтологии (GO, SO, ChEBI)

### Clarifier
Если данных мало - задаёт вопросы:
"Вы имеете в виду стабильную интеграцию или transient?"

### Dialog Manager
- Ведёт диалог
- Обновляет Goal Object
- Хранит контекст

### Validator
- pydantic-схема
- Проверка биологической валидности
- Проверка на противоречия

## Anti-hallucination

- LLM НЕ принимает биологических решений
- LLM только парсит язык и генерирует объяснения
- Все решения - движок на правилах и данных
- Каждое поле Goal Object - со ссылкой на источник

## Технологии

- Python 3.12
- LLM: Anthropic/OpenAI SDK или llama-cpp-python
- RAG: LlamaIndex / свой
- Embeddings: sentence-transformers
- Онтологии: pronto, owlready2
- Валидация: pydantic v2
