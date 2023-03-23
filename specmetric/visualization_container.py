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
    self.initial_node = initial_node
    self.computation_nodes = [initial_node]
    self.valid_chart = None
    self.encodings = {}
    self.compositions = compositions
    self.grammatical_expressions = grammatical_expressions
    self.parse_initial_node_preferences()

  def get_function_preferences(self):
    return [self.grammatical_expressions[n.function_type] for n in self.computation_nodes]

  def parse_initial_node_preferences(self):
    preferences = self.get_function_preferences()[0]

    # Get any other encodings from the node
    encoding_config = preferences['output_encoding_config']
    if encoding_config:
      self.update_encoding(self.initial_node.output_data, encoding_config)

  def parse_chart(self, chart_type, input_data, output_data):
    """
    Adds the encodings for the selected chart type.  
    """
    if chart_type == 'spacefilling':
      # input_data should be a vector name
      # We should take input data's encoding.  We won't have that just yet.
      # For now, I will just enforce that the child encoding gets squares
      self.update_encodings(
        input_data[0],
        {
          'mark': 'square',
          'channels': ['x', 'y', 'x2', 'y2']
        }
      )
      # Then, output data should be a scalar, encoded with an area
      self.update_encodings(
        output_data[0],
        {
          'mark': 'area',
          'channels': ['x', 'y', 'x2', 'y2']
        }
      )

      # The actual calculations of the values are calculated by the renderer
    elif chart_type == 'single_stacked_bar':
      # input_data are scalars, output_data is a single scalar
      # inputs are areas, output is area
      self.update_encodings(
        input_data[0],
        {
          'mark': 'area',
          'channels': ['x', 'y', 'x2', 'y2']
        }
      )

      self.update_encodings(
        input_data[1],
        {
          'mark': 'area',
          'channels': ['x', 'y', 'x2', 'y2']
        }
      )

      self.update_encodings(
        output_data[0],
        {
          'mark': 'area',
          'channels': ['x', 'y', 'x2', 'y2']
        }
      )
    elif chart_type == 'scatter_y_equals_x':
      # Inputs are points on scatterplot
      # outputs are lines
      self.update_encodings(
        input_data[0],
        {
          'mark': 'point',
          'channels': ['x', 'y']
        }
      )
      self.update_encodings(
        input_data[1],
        {
          'mark': 'point',
          'channels': ['x', 'y']
        }
      )
      self.update_encodings(
        output_data[0],
        {
          'mark': 'line',
          'channels': ['x', 'y', 'x2', 'y2']
        }
      )
    elif chart_type == 'bar_chart_diff':
      # inputs are scalars, output is scalar
      # each is a bar with x and y value
      self.update_encodings(
        input_data[0],
        {
          'mark': 'line',
          'channels': ['x', 'y']
        }
      )
      self.update_encodings(
        input_data[1],
        {
          'mark': 'line',
          'channels': ['x', 'y']
        }
      )
      self.update_encodings(
        output_data[0],
        {
          'mark': 'line',
          'channels': ['x', 'y']
        }
      )

  def update_encoding(self, attribute_name, encoding_config, overwrite=True):
    self.encodings[attribute_name] = self.encodings[attribute_name] or {}
    self.encodings[attribute_name].merge(encoding_config)

  # def add_computation_nodes(node):
  #   self.computation_nodes.append(node)

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

    if self.valid_chart and self.chart_reqs_met():
      self.initial_parse_chart(self.valid_chart, self.initial_node.input_data, self.initial_node.output_data)

    self.preferences = rule_match.resolve_preferences()
    self.add_computation_node(parent_node)
    return self
  
  def chart_reqs_met(self):
    