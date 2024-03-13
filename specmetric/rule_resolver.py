from specmetric.rules_config import compositions as _compositions
from specmetric.rules_config import grammatical_expressions as _grammatical_expressions

class VisualizationRule:
  """
  class responsible for determining what happens when we merge a new computation of "parent_type"
  with the existing set of preferences
  """
  def __init__(self, additional_preferences, child_type, parent_type, compositions=_compositions, grammatical_expressions=_grammatical_expressions):
    self.additional_preferences = additional_preferences
    self.child_type = child_type
    self.parent_type = parent_type
    self.compositions = compositions
    self.grammatical_expressions = grammatical_expressions
    self.valid = False
    self.resolve_parent_type()

  def resolve_parent_type(self):
    child_preferences = self.grammatical_expressions[self.child_type]
    parent_preferences = self.grammatical_expressions[self.parent_type]

    child_compositions = self.compositions['child_rules'][self.child_type]
    # First, check if data types work
    
    self.valid = ('any' in child_compositions) or (self.parent_type in child_compositions)
