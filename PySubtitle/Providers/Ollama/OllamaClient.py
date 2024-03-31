import logging

from PySubtitle.SubtitleError import TranslationResponseError

import ollama

from PySubtitle.Helpers import FormatMessages
from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt

class OllamaClient(TranslationClient):
    """
    Handles communication with Ollama to request translations
    """
    def __init__(self, settings : dict):
        super().__init__(settings)

        logging.info(f"Translating with Ollama model {self.model or 'default'}")

    @property
    def model(self):
        return self.settings.get('model')
    
    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        temperature = temperature or self.temperature
        response = self._send_messages(prompt.content, temperature)

        translation = Translation(response) if response else None

        if translation:
            if translation.reached_token_limit:
                raise TranslationError(f"Too many tokens in translation", translation=translation)

        return translation

    def _send_messages(self, messages : list[str], temperature):
        """
        Make a request to the Ollama API to provide a translation
        """
        response = {}

        try:
            result : ollama.ChatResponse = ollama.chat(
                model=self.model,
                messages=messages,
                options = { 
                    'temperature': temperature
                    }
            )

            if self.aborted:
                return None

            response['response_time'] = result.get('total_duration', 0) / 1000000
            response['eval_duration'] = result.get('eval_duration', 0) / 1000000
            response['prompt_tokens'] = result.get('prompt_eval_count', 0)
            response['output_tokens'] = result.get('eval_count', 0)

            message = result.get('message', {})
            if message.get('role') != "assistant":
                raise TranslationResponseError("Ollama response was not from the AI", response=result)
            
            response['text'] = message.get('content', None)

            return response
        
        except ollama.ResponseError as e:
            if not self.aborted:
                raise TranslationError(str(e), error=e)

        except Exception as e:
            raise TranslationImpossibleError(f"Unexpected error communicating with Ollama", error=e)

    def GetParser(self):
        return TranslationParser(self.settings)

    def _abort(self):
        # TODO cancel any ongoing requests
        return super()._abort()
