from typing import Dict
import traceback

# ------------------------SoupMonad--------------------------------------------
class SoupMonad:
  def __init__(self, value: object = None, error_status: Dict = None):
    self.value = value
    self.error_status = error_status

  def __repr__(self):
    return f"SoupMonad({self.value}, {self.error_status})"

  def unwrap(self):
    return self.value

  def find(self, *args) -> 'SoupMonad':
    if self.error_status:
      return SoupMonad(None, error_status=self.error_status)
    try:
      result = self.value.find(*args,)
      return SoupMonad(result)
    except Exception as e:
      failure_status = {
          'trace': traceback.format_exc(),
          'exc': e,
          'args': args,
      }
      return SoupMonad(None, error_status=failure_status)

  def findAll(self, *args) -> 'SoupMonad':
    if self.error_status:
      return SoupMonad(None, error_status=self.error_status)
    try:
      result = self.value.findAll(*args,)
      return SoupMonad(result)
    except Exception as e:
      failure_status = {
          'trace': traceback.format_exc(),
          'exc': e,
          'args': args,
      }
      return SoupMonad(None, error_status=failure_status)
    
  @staticmethod
  def wrap(value):
    return SoupMonad(value)
# ------------------------SoupMonad--------------------------------------------
