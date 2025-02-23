from openai.types.chat import ChatCompletion

from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.SubtitleError import TranslationRefusedError, TranslationResponseError

linesep = '\n'

class OpenAIReasoningClient(OpenAIClient):
    """
    Handles chat communication with OpenAI to request translations
    """
    def __init__(self, settings : dict):
        settings['supports_system_messages'] = True
        settings['supports_conversation'] = True
        settings['supports_reasoning'] = True
        settings['system_user_role'] = 'developer'
        super().__init__(settings)

    @property
    def reasoning_effort(self):
        return self.settings.get('reasoning_effort', "low")

    def _send_messages(self, messages : list[str], temperature):
        """
        Make a request to an OpenAI-compatible API to provide a translation
        """
        result = {}

        completion : ChatCompletion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            reasoning_effort=self.reasoning_effort
        )

        if self.aborted:
            return None

        if not isinstance(completion, ChatCompletion):
            raise TranslationResponseError(f"Unexpected response type: {type(completion).__name__}", response=completion)

        if not getattr(completion, 'choices'):
            raise TranslationResponseError("No choices returned in the response", response=completion)

        result['response_time'] = getattr(completion, 'response_ms', 0)

        if completion.usage:
            result['prompt_tokens'] = getattr(completion.usage, 'prompt_tokens')
            result['output_tokens'] = getattr(completion.usage, 'completion_tokens')
            result['total_tokens'] = getattr(completion.usage, 'total_tokens')
            completion_tokens_details = getattr(completion.usage, 'completion_tokens_details')
            if completion_tokens_details:
                result["reasoning_tokens"] = getattr(completion_tokens_details, 'reasoning_tokens')
                result["accepted_prediction_tokens"] = getattr(completion_tokens_details, 'accepted_prediction_tokens')
                result["rejected_prediction_tokens"] = getattr(completion_tokens_details, 'rejected_prediction_tokens')

        if not completion.choices:
            raise TranslationResponseError("No choices returned in the response", response=completion)

        choices = [choice for choice in completion.choices if choice.message and not choice.message.refusal]
        result['refusals'] = [choice.message.refusal for choice in completion.choices if choice.message and choice.message.refusal]

        if not choices:
            refusals = [choice.message.refusal for choice in completion.choices if choice.message and choice.message.refusal]
            raise TranslationRefusedError("Model refused to complete the request", refusal=refusals, result=result)

        choice = choices[0]
        reply = choice.message

        result['finish_reason'] = getattr(choice, 'finish_reason', None)
        result['text'] = getattr(reply, 'content', None)

        return result
