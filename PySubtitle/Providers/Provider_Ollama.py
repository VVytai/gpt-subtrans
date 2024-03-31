
from copy import deepcopy
import logging
import os

try:
    import ollama
    import subprocess
    import appdirs
    from pathlib import Path

    from PySubtitle.Helpers import GetEnvFloat
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationParser import TranslationParser
    from PySubtitle.TranslationProvider import TranslationProvider
    from PySubtitle.ProviderAction import ProviderAction
    from PySubtitle.SubtitleError import ProviderError

    from PySubtitle.Providers.Ollama.OllamaClient import OllamaClient

    class Provider_Ollama(TranslationProvider):
        name = "Ollama"

        information = """
        <p>Use a locally hosted AI model as a translator with <a href="https://ollama.com/">Ollama</a>.</p>
        <p>Ollama must be installed separately, along with the <a href="https://ollama.com/library">ollama model library</a> you want to use.</p>
        """

        information_noserver = """<p>The Ollama server is not running. Start the server manually or provide the path to the executable.</p>"""
        information_nomodels = """<p>To use Ollama you must download one or more models to use from the <a href="https://ollama.com/library">ollama model library</a></p>"""

        def __init__(self, settings : dict):
            super().__init__(self.name, {
                'ollama_path': settings.get('ollama_path') or self._get_ollama_path(),
                "model": settings.get('model') or os.getenv('OLLAMA_MODEL'),
                'temperature': settings.get('temperature', GetEnvFloat('OLLAMA_TEMPERATURE', 0.0))
            })

            self.refresh_when_changed = ['ollama_path', 'start_ollama', 'stop_ollama', 'refresh_models']

            self.ollama_models = []
            self.ollama_running = False
            self.ollama_process = None

        @property
        def ollama_path(self) -> Path:
            return self.settings.get('ollama_path')

        def GetTranslationClient(self, settings : dict) -> TranslationClient:
            if not self.ollama_running:
                self.StartServer()

            client_settings : dict = deepcopy(self.settings)
            client_settings.update(settings)
            client_settings.update({
                'supports_conversation': True,
                'supports_system_messages': False,
                'supports_system_prompt': True
                })
            return OllamaClient(client_settings)
        
        def GetAvailableModels(self) -> list[str]:
            if not self.ollama_models:
                return []
            
            model_list = [model.get('name') for model in self.ollama_models]
            return sorted(model_list)
        
        def GetParser(self):
            return TranslationParser(self.settings)
        
        def GetInformation(self):
            if not self.ollama_running:
                return f"{self.information}\n{self.information_noserver}"
            
            if not self.ollama_models:
                return f"{self.information}\n{self.information_nomodels}"

            return self.information
        
        def GetOptions(self) -> dict:
            options = {
                'ollama_path': (Path, "The path to the Ollama executable"),
            }

            if not self.ollama_models:
                self.FetchModels()

            if self.ollama_path and not self.ollama_running:
                options['Start Server'] = (ProviderAction(lambda: self.StartServer()), "Start the Ollama server")
            
            if self.ollama_running:
                if self.ollama_models:
                    options['model'] = (self.available_models, "The model to use for translations")
                    options['temperature'] = (float, "The temperature to use for translations (default 0.0)")

                options['Refresh Models'] = (ProviderAction(lambda: self.FetchModels()), "Refresh the list of models from the Ollama server")
                # options['Download Model'] = (ProviderAction(lambda: self.RequestModelDownload()), "Download a model from the Ollama library")

                if self.ollama_process:
                    options['Stop Server'] = (ProviderAction(lambda: self.StopServer()), "Stop the Ollama server")

            return options

        def FetchModels(self):
            """Fetch the list of available models from the ollama server"""
            try:
                if not self.ollama_running:
                    self.StartServer()

                models = ollama.list()
                self.ollama_models = models.get('models', []) if models else []
                self.ollama_running = True
                if self.ollama_models:
                    self._available_models = self.GetAvailableModels()

            except Exception as e:
                logging.info(f"Unable to retrieve ollama model list: {e}")
                self.ollama_running = False

        def StartServer(self):
            """ Start an ollama server in a subprocess """
            # Terminate existing processes
            if self.ollama_running:
                self.StopServer()

            try:
                self.ollama_process = subprocess.Popen([str(self.ollama_path), "serve"], stdout=subprocess.PIPE)
                self.ollama_running = True

            except Exception as e:
                logging.error(f"Unable to start ollama server: {e}")
                self.ollama_running = False
        
        def StopServer(self):
            """ Stop the ollama server if it is running and we started it """
            if self.ollama_running and self.ollama_process:
                self.ollama_process.terminate()
                self.ollama_running = False

        def PullModel(self, model_name : str):
            """ Download a model with ollama """
            try:
                if not self.ollama_running:
                    self.StartServer()

                ollama.pull(model_name)

                self.FetchModels()

                if model_name in self.available_models:
                    self.settings['model'] = model_name

            except Exception as e:
                raise ProviderError(f"Unable to create model: {e}", provider=self)

            finally:
                self.settings['pull_model'] = None

        def RequestModelDownload(self):
            """ Download a model from the ollama library """
            if not self.action_handler:
                raise ProviderError("No action handler for Ollama", provider=self)
            
            self.action_handler("Download Ollama Model")

        def _get_ollama_path(self):
            if os.getenv('OLLAMA_PATH'):
                return os.getenv('OLLAMA_PATH')

            if os.name == 'nt':
                install_path = appdirs.user_data_dir('Ollama', 'Programs')
                ollama_path = os.path.join(install_path, 'ollama.exe')
            else:
                ollama_path = '/usr/local/bin/ollama'

            return ollama_path

except ImportError:
    logging.info("Ollama SDK not installed. Ollama provider will not be available")
