import uuid
from collections import deque
import pandas as pd

FUNCTION_PREFERENCES = {
  'vector_sum': {
    'input_data_type': 'vector',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'area',
        'output_data_mark': 'space_filling',
        'channels': [
          {
            'channel': 'area',
            'field': 'value'
          }
        ]
      },
      {
        'input_data_mark': 'line',
        'output_data_mark': 'stacked_line',
        'channels': [
          {
            'channel': 'y',
            'field': 'value',        
          }
        ]
      }
    ]
  },
  'scalar_sum': {
    'input_data_type': 'scalar',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'area',
        'output_data_mark': 'space_filling'
      },
      {
        'input_data_mark': 'line',
        'output_data_mark': 'stacked_line'
      }
    ]
  },
  'vector_square': {
    'input_data_type': 'vector',
    'output_data_type': 'vector',
    'mark_priority': [
      {
        'input_data_mark': 'point',
        'output_data_mark': 'square'
      }
    ]
  },
  'scalar_square': {
    'input_data_type': 'scalar',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'line',
        'output_data_mark': 'square'
      }
    ]
  },

  'vector_square_root': {
    'input_data_type': 'vector',
    'output_data_type': 'vector',
    'mark_priority': [
      {
        'input_data_mark': 'any',
        'output_data_mark': 'square',
        'extra': ['encode_input_not_output']
      }
    ]
  },
  'scalar_square_root': {
    'input_data_type': 'scalar',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'any',
        'output_data_mark': 'square',
        'extra': ['encode_input_not_output']
      }
    ]
  },

  'vector_absolute': {
    'input_data_type': 'vector',
    'output_data_type': 'vector',
    'mark_priority': [
      {
        'input_data_mark': 'point',
        'output_data_mark': 'line',
        'extra': ['difference_from_zero']
      }
    ]
  },
  'scalar_absolute': {
    'input_data_type': 'scalar',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'line',
        'output_data_mark': 'line'
      }
    ]
  },

  'vector_difference': {
    'input_data_type': 'vector',
    'output_data_type': 'vector',
    'mark_priority': [
      {
        'input_data_mark': 'any',
        'output_data_mark': 'point',
        'encoding': 'scatter',
        'extra': [
          'show_y_equals_x'
        ]
      }
    ]
  },
  'scalar_difference': {
    'input_data_type': 'scalar',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'space_filling',
        'output_data_mark': 'space_filling',
        'extra': [
          'show_input_and_output'
        ]
      },
      {
        'input_data_mark': 'any',
        'output_data_mark': 'line',
        'encoding': 'bar',
        'extra': [
          'show_input_and_output'
        ]
      }
    ]
  },
  'ratio': {
    'input_data_type': 'scalar',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'any',
        'output_data_mark': 'same',
        'extra': [
          'show_division_line'
        ]
      }
    ]
  },
  'mean': {
    'input_data_type': 'vector',
    'output_data_type': 'scalar',
    'mark_priority': [
      {

        'input_data_mark': 'any',
        'output_data_mark': 'line',
        'extra': [
          'show_distribution'
        ]
      }
    ]
  },
  'median': {
    'input_data_type': 'vector',
    'output_data_type': 'scalar',
    'mark_priority': [
      {
        'input_data_mark': 'any',
        'output_data_mark': 'line',
        'extra': [
          'show_distribution'
        ]
      }
    ]
  },
  'broadcast': {
    'input_data_type': 'scalar',
    'output_data_type': 'vector',
    'mark_priority': [
    ]
  },
  'scalar': {
    'input_data_type': 'any',
    'output_data_type': 'scalar',
    'mark_priority': [
    ]
  },
  'vector': {
    'input_data_type': 'any',
    'output_data_type': 'vector',
    'mark_priority': [
    ]  
  }
  
}

FUNCTION_TYPES = list(FUNCTION_PREFERENCES.keys())

class AltairRenderer:
  """
  AltairRenderer takes in a list of resolved specifications and produces 
  a sequence of charts that should be cross-linked

  specifications should also include the data needed to render the visualization
  """

  def __init__(self, resolved_specifications, data_dict):
    self.resolved_specifications = resolved_specifications
    self.data_dict = data_dict

  def convert_to_charts(self):
    for spec in resolved_specifications:
      # Render altair chart, but make sure that we have all needed scales
      # defined, including colors, since they will be shared.

      # First, we build the data frame
      data = pd.DataFrame(

      )
      chart = alt.Chart()

class ComputationNode:
  """
  ComputationNode is a data structure that represents a node in a computation
  graph.  It contains references to upstream and downstream nodes.

  Collections of ComputationNode instances can be traversed to build visualization
  instances
  """

  def __init__(self, name, parent_node, function_type, children=None, input_data=None, output_data=None):
    self.name = name
    self.function_type = function_type
    self.uuid = uuid.uuid4()

    if parent_node and not isinstance(parent_node, str):
      self.parent_node = parent_node.uuid
    else:
      self.parent_node = parent_node

    if children is None:
      children = []
    
    if input_data is None:
      input_data = []

    if output_data is None:
      output_data = []

    self.input_data = input_data
    self.output_data = output_data
    self.children = children

  def set_parent(self, node_id):
    self.parent_node = node_id

  def add_child(self, node_id):
    self.children.append(node_id)

  def is_leaf(self):
    return len(self.children) == 0

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
    parent_preferences = FUNCTION_PREFERENCES[self.parent_type]
    parent_input_data_type = parent_preferences['input_data_type']
    parent_output_data_type = parent_preferences['output_data_type']
    parent_mark_priority = parent_preferences['mark_priority']

    # First, check if data types work
    # child_data_type = 
    # if self.preferences


class VisualizationContainer:
  """
  VisualizationContainer is a data structure that contains references to 
  its computational subgraph, the corresponding
  data being visualized, and any preferences for marks and channels from 
  its corresponding computation nodes.
  """  

  COLORS = ['red', 'blue', 'green', 'orange']
  SYMBOLS = ['whatever']

  def __init__(self, initial_node):
    self.computation_nodes = [initial_node]
    self.mark_type = 'point'
    self.mark_encodings = []
    self.preferences = {}
    self.parse_initial_node_preferences()

  def get_function_preferences(self):
    return [FUNCTION_PREFERENCES[n.function_type] for n in self.computation_nodes]

  def parse_initial_node_preferences(self):
    self.preferences = self.get_function_preferences()[0]
    if (len(self.preferences['mark_priority']) > 0):
      preference = self.preferences['mark_priority'][0]
      self.mark_type = preference['output_data_mark']
      self.mark_encodings.append({
        'channel': '',
        'field': ''
        })

  def add_computation_nodes(node):
    self.computation_nodes.append(node)

  def parent_mergeable(self, parent_node):
    rule_match = VisualizationRule(
      preferences=self.preferences,
      parent_type=parent_node.function_type
      )
    return rule_match.valid

  def merge_parent(self, parent_node):
    rule_match = VisualizationRule(
      preferences=self.preferences,
      parent_type=parent_node.function_type
    )

    self.preferences = rule_match.resolve_preferences()
    self.add_computation_node(parent_node)
    return self
  
class ComputationTreeParser:
  """
  Parses the abstract syntax tree of a computation, where each node is a 
  ComputationNode.  Generates a directed acyclic graph of 
  VisualizationContainers with consistent preferences.
  """
  # Class methods

  def resolve_containers(parent_node, visualization_container_list):
    """
    Resolves 1 to n visualization containers (representing subgraphs)
    of computation graph into a list of m visualization containers.  Ideally
    m == 1, and the n visualization containers were merged.  But if there is
    a conflict, then m could be > 1, and we would show multiple visualizations
    for that step of the computation graph.

    params
    - parent_node: ComputationNode representing the root of a subtree
    - visualization_container_list: VisualizationContainer[] - contains the
    resolved VisualizationContainer from each child of a given node

    returns VisualizationContainer[] - a (ideally unitary) list of visualization
    containers that are valid to pass to our AltairRenderer

    @test: imagine 2 encodings that are not compatible, but a 3rd they are both
    compatible with.  Should test all 3 scenarios.  Example is with r2:
    container with [scatterplot, x to y_i, y to y_hat_i] with 
    [mark, y_i, size, y_i_minus_y_bar_squared]
    and [mark, y_hat_i, size, y_i_minus_y_hat_i_squared] to result in two charts
    each one using the different mark definition, and with different colors
    """
    # greedy search, swallow up list
    merged_child_containers = []
    parent_conflict = False
    while(len(visualization_container_list) > 0):
      child_container = visualization_container_list.pop()
      if child_container.parent_mergeable(parent_node):
        merged_child_containers.append(child_container.merge_parent(parent_node))
      else:
        merged_child_containers.append(child_container)
        parent_conflict = True

    # Need something that fixes encodings, i.e. scales, colors
    # Let's try it without that for now, and see what happens
    # Similarly let's forget about cross-linking for now and just get it working

    print("parent_node: ", parent_node.uuid, " parent_conflict", parent_conflict, " and merged_child_containers is ", merged_child_containers)
    if parent_conflict:
      return [merged_child_containers, VisualizationContainer(parent_node)]
    else:
      return [merged_child_containers]


  # Instance methods
  def __init__(self, computation_tree, node_dict, data_dict):
    self.computation_tree = computation_tree
    # The dag is implemented as a list of lists - it's really a linked list
    # but where each node could be 1 or more visualizations where we can't
    # agree on what encoding to use, so we make multiple visualizations
    self.visualization_containers = []
    self.node_dict = node_dict
    self.data_dict = data_dict

  def parse_computation_tree(self):
    """
    Recursive parsing function.  

    Depth-first search.

    Each path from root to leaf is decomposed into a set of visualizations.

    At each branching point, on the way back from DFS, branches are either merged
    or split into multiple, parallel visualizations.

    Returns a list of visualization containers.
    """

    def parse_node(tree):
      """
      pops the root node.  Determines if it can be added to the current 
      visualization container or if it needs to be the start of a new one.
      then recursively parses its children passing either the current vis
      container or a newly created one for each child.

      Recursion invariant: parse_root should return a deque representing a DAG
      of visualizations for everything beneath tree, where the last element of
      the deque is the current visualization container.  
      """
      if tree.is_leaf():
        # We are at a leaf, there is no former visualization to connect to
        return [VisualizationContainer(tree)]
      else:
        # if we are not at a leaf, we should have >0 children
        child_container_heads = []
        resolved_child_tails = []
        for child_node_id in tree.children:
          child_node = self.node_dict[child_node_id]
          child_containers = parse_node(child_node)

          # head gets judged against parent
          head_container = child_containers.pop()
          child_container_heads.append(head_container)

          # tail goes into the stack together
          resolved_child_tails = resolved_child_tails + child_containers

        # We resolve the current node and the n child containers, which will 
        # result in either 1 visualization container (child and tree were merged)
        # or m<=n+1 containers, meaning either/or the child containers were incompatible
        # with the tree node, so we had to start a new visualization container, or the
        # child containers were not mergeable so they had to stay as separate visualizations

        # Then, we return the previous visualizations, and the visualization containers from
        # resolve_containers
        return resolved_child_tails + ComputationTreeParser.resolve_containers(tree, child_container_heads)

    self.visualization_containers = [parse_node(self.computation_tree)]



