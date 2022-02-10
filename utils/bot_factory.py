import os
import logging
import sys, getopt
from pathlib import Path
from rasa.utils.endpoints import EndpointConfig
from rasa.core.agent import Agent
from collections.abc import Mapping

logger = logging.getLogger(__name__)

DEFAULT_LANG = 'en'

SUPPORTED_LANGS = {
  DEFAULT_LANG: 'english',
   'bn': 'Bangla',
}


class LazyDict(Mapping):
  def __init__(self, *args, **kw):
    self._raw_dict = dict(*args, **kw)

  def __getitem__(self, key):
    value = self._raw_dict.__getitem__(key)
    if isinstance(value, tuple):
      func, arg = value
      result = func(arg)
      self._raw_dict.__setitem__(key, result)
      return result
    else:
      return value

  def __iter__(self):
    return iter(self._raw_dict)

  def __len__(self):
    return len(self._raw_dict)


class BotFactory:
  __instance = None

  def __init__(self):
    if BotFactory.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      BotFactory.__instance = self
      bots_dict = dict(
          (k, (self.__createInstance, k)) for k in SUPPORTED_LANGS.keys())
      print(type(bots_dict))
      self.dict = LazyDict(bots_dict)

  def __exists_model(self, path):
    return Path(path).is_file()

  def __get_model(self, lang):
    app_dir = os.getenv('APP_DIR')
    app_dir = "/home/financial_demo_multi_language"
    return '{}/models/chat-model-{}.tar.gz'.format(app_dir, lang)

  @staticmethod
  def getOrCreate(lang):
    if BotFactory.__instance == None:
      BotFactory()
    return BotFactory.__instance.dict[lang]

  @staticmethod
  def createAll():
    return dict(map(lambda x: (x, BotFactory.getOrCreate(x)), SUPPORTED_LANGS.keys()))

  def __createInstance(self, lang):
    if not lang in SUPPORTED_LANGS:
      logger.warning(
        f'Unsupported language: ${lang}. The default will be used: ${DEFAULT_LANG}')

    model = self.__get_model(lang)

    if not self.__exists_model(model):
      print('Model not found: "{}"'.format(model))
      sys.exit(2)

    url = os.getenv('ACTION_ENDPOINT')
    url = 'http://localhost:5056/webhook'
    print('action endpoint: "{}"'.format(url))
    agent = Agent.load(
        model,
        action_endpoint=EndpointConfig(url)
    )

    return agent
