from specmetric.rules_config import compositions, grammatical_expressions

class VisualizationRule:
  """
  class responsible for determining what happens when we merge a new computation of "parent_type"
  with the existing set of preferences
  """
  def __init__(self, preferences, parent_type):
    self.preferences = preferences
    self.parent_type = parent_type
    self.valid = False
    self.resolve_parent_type()

  def resolve_parent_type(self):
    parent_preferences = grammatical_expressions[self.parent_type]
    parent_input_data_type = parent_preferences['input_data_type']
    parent_output_data_type = parent_preferences['output_data_type']
    parent_mark_priority = parent_preferences['mark_priority']

    # First, check if data types work
    # child_data_type = 
    # if self.preferences


