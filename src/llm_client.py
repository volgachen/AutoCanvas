import logging
import os
import random
import asyncio
import time
from asyncio import CancelledError
from typing import Any, Optional
from datetime import datetime
from openai import AsyncOpenAI, BadRequestError, RateLimitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential
)

from app.services.database import db

_logger = logging.getLogger(__name__)


class LLMClient(AsyncOpenAI):
    def _extract_retry_after(self, error) -> Optional[float]:
        """从错误响应中提取retry-after时间（秒）"""
        try:
            # 尝试从响应头中获取retry-after
            if hasattr(error, 'response') and hasattr(error.response, 'headers'):
                headers = error.response.headers
                if 'retry-after' in headers:
                    retry_after = headers['retry-after']
                    try:
                        return float(retry_after)
                    except ValueError:
                        # 可能是日期格式
                        from email.utils import parsedate_to_datetime
                        retry_date = parsedate_to_datetime(retry_after)
                        return (retry_date - datetime.now()).total_seconds()
            
            # 尝试从错误消息中提取
            error_msg = str(error)
            import re
            retry_match = re.search(r'retry.*?after.*?(\d+)', error_msg.lower())
            if retry_match:
                return float(retry_match.group(1))
                
        except Exception:
            pass
        
        return None

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=60),  # 指数退避
        stop=stop_after_attempt(5),  # 最多重试5次
        reraise=True,
        before_sleep=lambda retry_state: _rate_limit_sleep_handler(retry_state),
        retry=retry_if_not_exception_type((BadRequestError, CancelledError)),
    )
    async def generate(
        self,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ):
        # Get model name from parameter, kwargs, or instance attribute
        model_name = model or kwargs.pop("model", None) or getattr(self, "model_name", "unknown")

        # Log the LLM call before making the request
        call_record = db.create_llm_call(
            model_name=model_name,
            messages=kwargs["messages"],
            session_id=session_id,
            agent_name=agent_name,
        )
        call_id = call_record['id']
        start_time = time.time()

        try:
            response = await self.chat.completions.create(
                model=model_name,
                timeout=60.0,
                **kwargs,
            )
            duration_ms = int((time.time() - start_time) * 1000)
            response_content = response.choices[0].message.content

            # Extract token usage if available
            input_tokens = None
            output_tokens = None
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', None)
                output_tokens = getattr(response.usage, 'completion_tokens', None)

            # Update the call record with response
            db.update_llm_call(
                call_id=call_id,
                response=response_content,
                duration_ms=duration_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            return response_content, None

        except RateLimitError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            db.update_llm_call(
                call_id=call_id,
                error=f"RateLimitError: {str(e)}",
                duration_ms=duration_ms,
            )

            # 专门处理RateLimitError
            retry_after = self._extract_retry_after(e)

            if retry_after:
                wait_time = retry_after + random.uniform(0.1, 0.5)  # 添加随机抖动
                _logger.warning(
                    f"Rate limit hit for {self.model_name}. "
                    f"Retrying after {wait_time:.2f} seconds. "
                )
                await asyncio.sleep(wait_time)
            else:
                # 如果没有明确的retry-after，使用指数退避
                self._rate_limit_retries += 1
                wait_time = min(2 ** self._rate_limit_retries + random.random(), 60)
                _logger.warning(
                    f"Rate limit hit for {self.model_name} (no retry-after header). "
                    f"Retry {self._rate_limit_retries}, waiting {wait_time:.2f} seconds. "
                )
                await asyncio.sleep(wait_time)

            # 重新抛出异常以便retry装饰器继续处理
            raise

        except BadRequestError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            db.update_llm_call(
                call_id=call_id,
                error=f"BadRequestError: {str(e)}",
                duration_ms=duration_ms,
            )
            # BadRequestError通常表示无效请求，不应该重试
            _logger.error(f"Bad request error for {self.model_name}: {e}")
            return None, str(e)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            db.update_llm_call(
                call_id=call_id,
                error=f"{type(e).__name__}: {str(e)}",
                duration_ms=duration_ms,
            )
            # 其他异常
            _logger.error(f"Unexpected error for {self.model_name}: {e}")
            raise


def _rate_limit_sleep_handler(retry_state):
    """自定义的rate limit错误处理函数"""
    if retry_state.outcome and retry_state.outcome.failed:
        exc = retry_state.outcome.exception()
        if isinstance(exc, RateLimitError):
            # 记录详细信息
            # _logger.warning(
            #     f"Rate limit retry {retry_state.attempt_number} "
            #     f"for {retry_state.fn.__name__ if hasattr(retry_state.fn, '__name__') else 'unknown'}"
            # )
            pass


async def main():
    client = LLMClient(
        base_url=os.environ.get("OPENAI_BASE_URL", ""),
        api_key=os.environ.get("OPENAI_API_KEY", "")
    )

    response = await client.generate(
        model="gpt-4.1-mini",
        messages = [{"role": "user", "content": "Where am I?"}],
    )
    print(response)


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
