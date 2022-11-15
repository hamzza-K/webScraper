from typing import Dict
import traceback

class SeleMonad:
  """A Monadic Class for Selenium."""
  def __init__(self, value: object=None, contains_value: bool=True, error_status: Dict=None):
    self.value = value
    self.error_status = error_status
    self.contains_value = contains_value

  def __repr__(self):
    return f"SeleMonad({self.value},{self.error_status})"

  def unwrap(self):
    return self.value

  def find_element(self, *args) -> 'SeleMonad':
    if self.error_status:
      return SeleMonad(None, contains_value=False, error_status=self.error_status)
    try:
      result = self.value.find_element(*args)
      assert result != None
      return SeleMonad(result)
    except Exception as e:
      failure_status = {
          'trace': traceback.format_exc(),
          'exc': e,
          'args': args,
      }
      return SeleMonad(None, contains_value=False, error_status=failure_status)

  def find_elements(self, *args) -> 'SeleMonad':
    if self.error_status:
      return SeleMonad(None, contains_value=False, error_status=self.error_status)
    try:
      result = self.value.find_elements(*args,)
      return SeleMonad(result)
    except Exception as e:
      failure_status = {
          'trace': traceback.format_exc(),
          'exc': e,
          'args': args
      }
      return SeleMonad(None, contains_value=False, error_status=failure_status)