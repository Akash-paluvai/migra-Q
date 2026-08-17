# LLM Provider Retry Storm Fix

## 1. Remove Nested Retries
- `backend/translator/service.py` has a `while attempts <= max_retries:` loop that instantly retries `provider.generate_translation`.
- `backend/translator/provider.py` has a `for attempt in range(1, max_retries + 1):` loop.
- I will remove the retry loop in `backend/translator/service.py` and `backend/diagnosis_ai/service.py`. The provider handles HTTP backoff (`429` etc) and transient network errors. The service layer should not blindly retry all exceptions instantly.

## 2. Handle HTTP 400 (Bad Request)
- In `backend/translator/provider.py` (and `diagnosis_ai/provider.py`), HTTP 400 indicates a bad prompt or schema. It is NOT a transient error. It should instantly break and fail without retries.

## 3. Handle HTTP 429 Backoff
- The provider currently handles 429 with exponential backoff (`time.sleep(retry_delay)`). This is correct, but since `service.py` was also retrying instantly on the final exception, it caused a rapid retry storm. Removing `service.py`'s loop fixes this.

## 4. Structured Output Format
- The user suggested checking if we omit `strict: True`. We *are* using `strict: True` in `backend/translator/provider.py`. However, for `openai/gpt-oss-120b`, Groq might still return 400 if the schema is rejected or if the output gets cut off due to max tokens.
- I will change the structured output format for Groq to just `{"type": "json_object"}` since it's more stable, or keep `strict: True` but ensure the JSON schema is perfectly compliant. I will just keep `strict: True` as is since the user said "test strict=True with a schema compliant with Groq's requirements", which we already have. If the prompt/schema is the issue, it will fail fast instead of spamming 400s.

## 5. Token Limit Check
- The user noticed 2037 input + 1500 output = 3537 tokens. I will leave `max_tokens` at 1500 for now, as the main issue was the retry storm caused by nested loops.

