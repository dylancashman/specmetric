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

  def __init__(self, initial_node, valid_chart=None, compositions=_compositions, grammatical_expressions=_grammatical_expressions):
    self.initial_node = initial_node
    self.computation_nodes = [initial_node]
    self.valid_chart = valid_chart
    self.encodings = {}
    self.compositions = compositions
    self.grammatical_expressions = grammatical_expressions
    self.parse_node_preferences(initial_node)

  def get_function_preferences(self, function_type):
    return self.grammatical_expressions[function_type]

  def get_node_preferences(self, node):
    return self.get_function_preferences(node.function_type)

  def parse_node_preferences(self, node):
    preferences = self.get_node_preferences(node)

    # Get any other encodings from the node
    encoding_config = preferences['output_encoding_config']
    if encoding_config:
      self.update_encoding(node.output_data, encoding_config)

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
    """
    Parent is mergeable if any of the following is true

    1) parent_node does not have a valid visualization
    or
    2) container_does not have a valid visualization
    or
    3) They both do, but a rule exists to merge them.

    """
    # get parent valid_chart
    parent_preferences = get_function_preferences(parent_node.function_type)
    parent_valid_chart = parent_preferences['valid_visualization']

    # get self valid_chart
    child_valid_chart = self.valid_chart

    if not parent_valid_chart:
    # check condition 1
      return True
    elif not child_valid_chart:
    # check condition 2
      return True
    else:
    # check condition 3
      return charts_mergeable(parent_valid_chart, child_valid_chart)

  def charts_mergeable(self, parent_chart, child_chart):
    """
    Returns true if there is a valid composition rule from child to parent, false otherwise
    """
    # For now, we hardcode the matches here
    return ((parent_chart == 'spacefilling') and (child_chart == 'bar_chart_comp')) or 
           ((parent_chart == 'spacefilling') and (child_chart == 'single_stacked_bar')) or 
           ((parent_chart == 'spacefilling') and (child_chart == 'bar_chart_diff'))

    # rule_match = VisualizationRule(
    #   preferences=self.preferences,
    #   parent_type=parent_node.function_type,
    #   compositions=compositions,
    #   grammatical_expressions=grammatical_expressions
    #   )
    # return rule_match.valid

  def merge_chart_types(self, parent_node, child_node):
    """
    Handles all the logic of merging chart types. 
    1. Set's the valid chart variable
    2. Adds/modifies any additional encodings
    """

    # For now, we hardcode the matches here
    parent_preferences = self.get_node_preferences(parent_node)
    child_preferences = self.get_node_preferences(child_node)
    parent_chart = parent_preferences['valid_chart']
    child_chart = child_preferences['valid_chart']

    # what is the resulting chart, and what encodings do we need
    if ((parent_chart == 'spacefilling') and (child_chart == 'bar_chart_comp')):
      self.merge_spacefilling_bar_chart_comp(parent_node, child_node)
    elif ((parent_chart == 'spacefilling') and (child_chart == 'single_stacked_bar')):
      self.merge_spacefilling_single_stacked_bar(parent_node, child_node)
    elif ((parent_chart == 'spacefilling') and (child_chart == 'bar_chart_diff')):
      self.merge_spacefilling_bar_chart_diff(parent_node, child_node)

  def merge_spacefilling_bar_chart_comp(self, bar_chart_node, spacefilling_node):
    self.valid_chart = 'bar_chart_comp'
    # building a more complicated bar chart comp

    # The spacefilling areas need to get an offset so they appear in the barchart
    output_data_var = spacefilling_node['output_data']

    # update_encoding(self, attribute_name, encoding_config, overwrite=True):
      #     self.update_encodings(
      #   output_data[0],
      #   {
      #     'mark': 'area',
      #     'channels': ['x', 'y', 'x2', 'y2']
      #   }
      # )
    spacefilling_params = self.encodings[output_data_var]
    self.update_encodings(
      output_data_var,
      {
        'mark': 'area',
        'channels': ['x', 'y', 'x2', 'y2'],
        'offset': 'tied' # @TODO - how to express this in my DSL?
      }
    )



  def merge_spacefilling_single_stacked_bar(self, bar_node, spacefilling_node):
    self.valid_chart = 'single_stacked_bar'
    # The spacefilling areas need to get an offset so they appear in the single bar
    pass

  def merge_spacefilling_bar_chart_diff(self, bar_chart_node, spacefilling_node):
    self.valid_chart = 'bar_chart_diff'
    # The spacefilling areas need to get an offset so they appear in the corresponding bars
    pass

  def merge_parent(self, parent_node):
    """
    @TODO
    Precondition: 
    1) parent_node does not have a valid visualization
    or
    2) container_does not have a valid visualization
    or
    3) They both do, but a rule exists to merge them.

    If 1) or 2), we merge the preferences from the parent node into the child node and return
    If 3), we follow the rule for what the ensuing valid chart would be, and also merge the
    visualization preferences.
    """
    # Get parent preferences, including valid chart
    parent_preferences = get_function_preferences(parent_node.function_type)
    parent_valid_chart = parent_preferences['valid_visualization']

    # get self valid_chart
    child_valid_chart = self.valid_chart

    # get the base parent chart preferences
    self.parse_node_preferences(parent_node)

    # check condition 1
    if not parent_valid_chart:
      # we leave the child's chart as is
      # and we inherit any preferences from the parent
      pass
    # check condition 2
    elif not child_valid_chart:
      # we only take the parent chart if it has valid data
      # @TODO
      # # When inheriting valid chart from parent node, need to check that it is actually
      # # valid, i.e. the children have been picked for encoding
      if self.valid_chart and self.chart_reqs_met(parent_node):
        self.initial_parse_chart(self.valid_chart, self.initial_node.input_data, self.initial_node.output_data)
    # then condition 3
    else:
      #  get resulting chart, set valid chart, update preferences, etc.
      merge_chart_types(parent_preferences, self.preferences) 
  
  def chart_reqs_met(self, parent_node):
    #@todo
    # Check if the input data from the valid_chart type of the parent
    # is all marked to be encoded, i.e. it should be visualized
    return True