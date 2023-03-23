import uuid

class ComputationNode:
  """
  ComputationNode is a data structure that represents a node in a computation
  graph.  It contains references to upstream and downstream nodes.

  Collections of ComputationNode instances can be traversed to build visualization
  instances
  """

  def __init__(self, name, parent_node, function_type, input_data=None, output_data=None):
    self.name = name
    self.function_type = function_type
    self.uuid = uuid.uuid4()

    if parent_node:
      self.parent_node = parent_node
      self.parent_node.add_child(self)

    if input_data is None:
      input_data = []

    if output_data is None:
      output_data = []

    self.input_data = input_data
    self.output_data = output_data
    self.children = []

  def set_parent(self, node_id):
    self.parent_node = node_id

  def add_child(self, node_id):
    self.children.append(node_id)

  def is_leaf(self):
    return len(self.children) == 0


