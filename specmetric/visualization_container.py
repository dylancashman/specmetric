from specmetric.rule_resolver import VisualizationRule
from specmetric.rules_config import compositions as _compositions
from specmetric.rules_config import grammatical_expressions as _grammatical_expressions
import json

class VisualizationContainer:
  """
  VisualizationContainer is a data structure that contains references to 
  its computational subgraph, the corresponding
  data being visualized, and any preferences for marks and channels from 
  its corresponding computation nodes.
  """  

  def __init__(self, root_node, child_encodings={},compositions=_compositions, grammatical_expressions=_grammatical_expressions, lowest_depth=0):
    self.root_node = root_node
    self.computation_nodes = [root_node]
    self.lowest_depth = lowest_depth
    self.valid_chart = None
    self.encodings = {}
    self.child_encodings = child_encodings
    self.compositions = compositions
    self.grammatical_expressions = grammatical_expressions
    self.parse_node_preferences(root_node, initial=True)
    self.parse_chart(self.valid_chart, self.root_node.input_data, self.root_node.output_data)

  # DEBUGGING PURPOSES
  def __repr__(self):
    return "(VisualizationContainer - valid_chart: {}, root_node: {}, lowest_depth: {})".format(self.valid_chart, self.root_node.name, self.lowest_depth)

  def pp(self):
    print("""
    VisualizationContainer
    ----------
    valid_chart: {}
    root_node: {}
    lowest_depth: {}
    computation_nodes: ({})
    encodings:
    {}
    """.format(self.valid_chart, self.root_node.name, self.lowest_depth, [n.name for n in self.computation_nodes], json.dumps(self.encodings, indent=4)))

  def get_function_preferences(self, function_type):
    return self.grammatical_expressions[function_type]

  def get_node_preferences(self, node):
    return self.get_function_preferences(node.function_type)

  def parse_node_preferences(self, node, initial=False):
    preferences = self.get_node_preferences(node)

    if initial and ('valid_visualization' in preferences):
      self.valid_chart = preferences['valid_visualization']

    # Get any encodings from the node
    if 'output_encoding_config' in preferences:
      self.update_encoding(node.output_data, preferences['output_encoding_config'])

  def parse_chart(self, chart_type, input_data, output_data):
    """
    Adds the encodings for the selected chart type.  
    """
    # print("parsing chart with chart_type", chart_type)
    if chart_type == 'spacefilling':
      # input_data should be a vector name
      # We should take input data's encoding.  We won't have that just yet.
      # For now, I will just enforce that the child encoding gets squares
      self.update_encoding(
        input_data[0],
        {
          'mark': 'square',
          'channels': 'vector-location'
        }
      )
      # Then, output data should be a scalar, encoded with an area
      # self.update_encoding(
      #   output_data,
      #   {
      #     'mark': 'area',
      #     'channels': 'vector-location'
      #   }
      # )
      # Actually, we don't explicitly encode the output in a spacefilling
      # visualization - it is implicit.
      # Although we might need to tell it about the value of the output...
      # for scales.  Let's see.

      # The actual calculations of the values are calculated by the renderer
    elif chart_type == 'single_stacked_bar':
      # input_data are scalars, output_data is a single scalar
      # inputs are areas, output is area
      self.update_encoding(
        input_data[0],
        {
          'mark': 'area',
          'channels': 'scalar-location'
        }
      )

      self.update_encoding(
        input_data[1],
        {
          'mark': 'area',
          'channels': 'scalar-location'
        }
      )

      # self.update_encoding(
      #   output_data,
      #   {
      #     'mark': 'area',
      #     'channels': ['x', 'y', 'x2', 'y2']
      #   }
      # )
    elif chart_type == 'scatter_y_equals_x':
      # Inputs are points on scatterplot
      # outputs are lines

      # Need to check to see if the input data is already in the encoding
      # and if it isn't, leave the encoding as blank
      # so that a future merge can take over the encoding
      # hmmmm.  Not sure where this takes place.  But we probably should
      # only use one encoding for x and y for all merged charts.  Complicated.
      # Or rather for all vector encodings.  But what is to say we use 
      # that one over this one.
      self.update_encoding(
        input_data[0],
        {
          'mark': 'point',
          'channels': 'vector-location',
          'preference': 'x'
        }
      )
      self.update_encoding(
        input_data[1],
        {
          'mark': 'point',
          'channels': 'vector-location',
          'preference': 'y'
        }
      )
      self.update_encoding(
        output_data,
        {
          'mark': 'line',
          'channels': 'vector-location'
        }
      )
    elif chart_type == 'bar_chart_diff':
      # inputs are scalars, output is scalar
      # each is a bar with x and y value
      self.update_encoding(
        input_data[0],
        {
          'mark': 'line',
          'channels': 'scalar-location'
        }
      )
      self.update_encoding(
        input_data[1],
        {
          'mark': 'line',
          'channels': 'scalar-location'
        }
      )
      # self.update_encoding(
      #   output_data,
      #   {
      #     'mark': 'line',
      #     'channels': ['x', 'y']
      #   }
      # )
    elif chart_type == 'bar_chart_comp':
      self.update_encoding(
        input_data[0],
        {
          'mark': 'line',
          'channels': 'scalar-location'
        }
      )
      self.update_encoding(
        input_data[1],
        {
          'mark': 'line',
          'channels': 'scalar-location'
        }
      )
    elif chart_type == 'mean_chart':
      if input_data[0] not in self.child_encodings:
        # We can't build this chart for a non-encoded attribute
        # We reset everything
        print("input_data[0]", input_data[0], " is not in self.encodings", self.child_encodings)
        self.valid_chart = None
      else:
        print("mean encoding was found")
        input_data_encoding = self.child_encodings[input_data[0]]['mark']
        self.update_encoding(
          input_data[0],
          {
            'mark': input_data_encoding,
            'channels': 'vector-location'
          }
        )

  # def validate_visualization(self):
  #   """
  #   Conducts some checks to make sure that a visualization doesn't need any 
  #   additional encodings.  This can happen if a visualization has marks for a
  #   vector, but doesn't yet have those attributes encoded (i.e. a scatter plot
  #   but we only have 1 dimension defined)
  #   """
  #   if self.valid_chart == 'scatter_y_equals_x':
  #     proposed_x_encoding = None
  #     proposed_y_encoding = None
  #     for (encoding, conf) in self.encodings.items():
  #       if conf['preference'] == 'x':
  #         proposed_x_encoding = encoding
  #       elif conf['preference'] == 'y':
  #         proposed_y_encoding = encoding

  #     if 


  def update_encoding(self, attribute_name, encoding_config, overwrite=True):
    # print("here, self.encodings is ", self.encodings, " and attribute_name is ", attribute_name)
    if attribute_name not in self.encodings:
      self.encodings[attribute_name] = {}
    self.encodings[attribute_name] = self.encodings[attribute_name] | encoding_config

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
    parent_preferences = self.get_function_preferences(parent_node.function_type)
    parent_valid_chart = parent_preferences.get('valid_visualization')

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
      return self.charts_mergeable(parent_valid_chart, child_valid_chart)

  def charts_mergeable(self, parent_chart, child_chart):
    """
    Returns true if there is a valid composition rule from child to parent, false otherwise
    """
    # For now, we hardcode the matches here
    return (((child_chart == 'spacefilling') and (parent_chart == 'bar_chart_comp')) 
            or ((child_chart == 'spacefilling') and (parent_chart == 'single_stacked_bar')) 
            or ((child_chart == 'spacefilling') and (parent_chart == 'bar_chart_diff')))

  def merge_chart_types(self, parent_node):
    """
    Handles all the logic of merging chart types. 
    1. Set's the valid chart variable
    2. Adds/modifies any additional encodings
    """

    # For now, we hardcode the matches here
    parent_preferences = self.get_node_preferences(parent_node)
    child_encodings = self.encodings
    parent_chart = parent_preferences.get('valid_visualization')
    child_chart = self.valid_chart
    # print("parent_node.name is ", parent_node.name, " parent_node is ", parent_node.function_type, ".  child root is ", self.root_node.name, " merging chart types ", parent_chart, " and ", child_chart)
    # what is the resulting chart, and what encodings do we need
    if ((child_chart == 'spacefilling') and (parent_chart == 'bar_chart_comp')):
      self.merge_spacefilling_bar_chart_comp(parent_node, self.root_node)
    elif ((child_chart == 'spacefilling') and (parent_chart == 'single_stacked_bar')):
      self.merge_spacefilling_single_stacked_bar(parent_node, self.root_node)
    elif ((child_chart == 'spacefilling') and (parent_chart == 'bar_chart_diff')):
      self.merge_spacefilling_bar_chart_diff(parent_node, self.root_node)

  def merge_spacefilling_bar_chart_comp(self, bar_chart_node, spacefilling_node):
    self.valid_chart = 'bar_chart_comp'
    # building a more complicated bar chart comp
    # print("should be spacefilling barchart comp")
    # The spacefilling areas need to get an offset so they appear in the barchart
    spacefilling_var = spacefilling_node.output_data
    bar_chart_var = bar_chart_node.output_data

    self.update_encoding(
      spacefilling_var,
      {
        'mark': 'area',
        'channels': ['x', 'y', 'x2', 'y2'],
        'offset': 'tied-' + bar_chart_var # i.e. offset position by the corresponding bar location.  To be handled by the renderer.
      }
    )

  def merge_spacefilling_single_stacked_bar(self, bar_node, spacefilling_node):
    self.valid_chart = 'single_stacked_bar'
    
    # The spacefilling areas need to get an offset so they appear in the single bar
    spacefilling_var = spacefilling_node.output_data
    bar_var = bar_node.output_data

    self.update_encoding(
      spacefilling_var,
      {
        'mark': 'area',
        'channels': ['x', 'y', 'x2', 'y2'],
        'offset': 'tied-' + bar_var # i.e. offset position by the corresponding bar location.  To be handled by the renderer.
      }
    )

  def merge_spacefilling_bar_chart_diff(self, bar_chart_node, spacefilling_node):
    self.valid_chart = 'bar_chart_diff'

    # The spacefilling areas need to get an offset so they appear in the corresponding bars
    spacefilling_var = spacefilling_node.output_data
    bar_chart_var = bar_chart_node.output_data

    self.update_encoding(
      spacefilling_var,
      {
        'mark': 'area',
        'channels': ['x', 'y', 'x2', 'y2'],
        'offset': 'tied-' + bar_chart_var # i.e. offset position by the corresponding bar location.  To be handled by the renderer.
      }
    )

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
    parent_preferences = self.get_function_preferences(parent_node.function_type)
    parent_valid_chart = parent_preferences.get('valid_visualization')

    # get self valid_chart

    # get the base parent chart preferences
    self.parse_node_preferences(parent_node)
    child_valid_chart = self.valid_chart
    # print("child_valid_chart is ", child_valid_chart)
    # print("parent_valid_chart is ", parent_valid_chart)

    # check condition 1
    if not parent_valid_chart:
      # we leave the child's chart as is
      # and we inherit any preferences from the parent
      pass
    # check condition 2
    elif not child_valid_chart:
      # we only take the parent chart if it has valid data
      # # When inheriting valid chart from parent node, need to check that it is actually
      # # valid, i.e. the children have been picked for encoding
      # print("checking if reqs met")
      if self.chart_reqs_met(parent_node):
        self.valid_chart = parent_valid_chart
        # print("reqs were met")
        # self.parse_chart(parent_valid_chart, parent_node.input_data, parent_node.output_data)
        # print(" OK, and now what is my valid chart?  ", self.valid_chart)
    # then condition 3
    else:
      #  get resulting chart, set valid chart, update preferences, etc.
      self.merge_chart_types(parent_node) 
  
  def add_node(self, node):
    self.computation_nodes.append(node)

  def chart_reqs_met(self, parent_node):
    # Check if the input data from the valid_chart type of the parent
    # is all marked to be encoded, i.e. it should be visualized
    # This is to catch when an unexpected/uncovered function is used, like
    # np.fill(), which we don't currently have a visual analog for.
    # Or if a chart only makes sense if you have a certain encoding for
    # the input data
    parent_preferences = self.get_function_preferences(parent_node.function_type)
    if ('valid_visualization' in parent_preferences) and parent_preferences['valid_visualization'] == 'mean_chart':
      return all([((d in self.encodings) and (m in ['line', 'square'] for m in self.encodings[d]['mark'])) for d in parent_node.input_data])
    else:
      return True