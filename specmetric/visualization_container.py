from specmetric.rule_resolver import VisualizationRule
from specmetric.rules_config import compositions as _compositions
from specmetric.rules_config import grammatical_expressions as _grammatical_expressions

class VisualizationContainer:
  """
  VisualizationContainer is a data structure that contains references to 
  its computational subgraph, the corresponding
  data being visualized, and any preferences for marks and channels from 
  its corresponding computation nodes.
  """  

  def __init__(self, initial_node, compositions=_compositions, grammatical_expressions=_grammatical_expressions):
    self.computation_nodes = [initial_node]
    self.mark_type = 'point'
    self.mark_encodings = []
    self.preferences = {}
    self.compositions = compositions
    self.grammatical_expressions=grammatical_expressions
    self.parse_initial_node_preferences()

  def get_function_preferences(self):
    return [self.grammatical_expressions[n.function_type] for n in self.computation_nodes]

  def parse_initial_node_preferences(self):
    self.preferences = self.get_function_preferences()[0]
    if (len(self.preferences['mark_priority']) > 0):
      preference = self.preferences['mark_priority'][0]
      self.mark_type = preference['output_data_mark']
      # self.mark_encodings.append({
      #   'channel': '',
      #   'field': ''
      #   })

  def add_computation_nodes(node):
    self.computation_nodes.append(node)

  def parent_mergeable(self, parent_node):
    rule_match = VisualizationRule(
      preferences=self.preferences,
      parent_type=parent_node.function_type,
      compositions=compositions,
      grammatical_expressions=grammatical_expressions
      )
    return rule_match.valid

  def merge_parent(self, parent_node):
    rule_match = VisualizationRule(
      preferences=self.preferences,
      parent_type=parent_node.function_type,
      compositions=compositions,
      grammatical_expressions=grammatical_expressions
    )

    self.preferences = rule_match.resolve_preferences()
    self.add_computation_node(parent_node)
    return self
  
