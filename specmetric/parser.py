from specmetric.visualization_container import VisualizationContainer
from specmetric.rules_config import compositions as _compositions
from specmetric.rules_config import grammatical_expressions as _grammatical_expressions

class ComputationTreeParser:
  """
  Parses the abstract syntax tree of a computation, where each node is a 
  ComputationNode.  Generates a directed acyclic graph of 
  VisualizationContainers with consistent preferences.
  """
  # Class methods

  def mergeFamily(parent_node, visualization_container_list, compositions=_compositions, grammatical_expressions=_grammatical_expressions, parent_depth=0):
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
    - compositions: set of grammar composition rules

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
    unmerged_child_containers = []

    # First, we need to get all children, and get their encodings
    child_encodings = {}
    for child_container in visualization_container_list:
      child_encodings = child_encodings | child_container.encodings

    parent_container = VisualizationContainer(parent_node, child_encodings=child_encodings, compositions=compositions, grammatical_expressions=grammatical_expressions, lowest_depth=parent_depth)

    while(len(visualization_container_list) > 0):
      child_container = visualization_container_list.pop()
      if child_container.lowest_depth < parent_container.lowest_depth:
        child_container.lowest_depth = parent_container.lowest_depth

      if child_container.parent_mergeable(parent_node):
        child_container.merge_parent(parent_node)
        # The child container has invaded the parent container and taken over
        for node in parent_container.computation_nodes:
          child_container.add_node(node)

        # we also need to copy over metadata from the parent
        # this should really be all one subroutine, but thats for refactoring
        child_container.encodings = child_container.encodings | parent_container.encodings
        child_container.root_node = parent_container.root_node

        parent_container = child_container
      else:
        unmerged_child_containers.append(child_container)

    unmerged_child_containers.append(parent_container)
    return unmerged_child_containers


  # Instance methods
  def __init__(self, computation_tree, compositions=_compositions, grammatical_expressions=_grammatical_expressions):
    self.computation_tree = computation_tree
    # The dag is implemented as a list of lists - it's really a linked list
    # but where each node could be 1 or more visualizations where we can't
    # agree on what encoding to use, so we make multiple visualizations
    self.visualization_containers = []
    self.compositions = compositions
    self.grammatical_expressions = grammatical_expressions

  def visualizeDFG(self):
    """
    Recursive parsing function.  

    Depth-first search.

    Each path from root to leaf is decomposed into a set of visualizations.

    At each branching point, on the way back from DFS, branches are either merged
    or split into multiple, parallel visualizations.

    Returns a list of visualization containers.
    """

    def parseDFTree(tree, depth=0):
      """
      pops the root node.  Determines if it can be added to the current 
      visualization container or if it needs to be the start of a new one.
      then recursively parses its children passing either the current vis
      container or a newly created one for each child.

      Recursion invariant: parse_root should return a deque representing a DAG
      of visualizations for everything beneath tree, where the last element of
      the deque is the current visualization container.  
      """
      new_depth = depth + 1
      if tree.is_leaf():
        # We are at a leaf, there is no former visualization to connect to
        return [VisualizationContainer(tree, compositions=self.compositions, grammatical_expressions=self.grammatical_expressions, lowest_depth=new_depth)]
      else:
        # if we are not at a leaf, we should have >0 children
        child_container_heads = []
        resolved_child_tails = []
        for child_node in tree.children:
          child_containers = parseDFTree(child_node, depth=new_depth)

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
        # mergeFamily
        resolved_child_tails = sorted(resolved_child_tails + ComputationTreeParser.mergeFamily(tree, child_container_heads, self.compositions, self.grammatical_expressions, parent_depth=new_depth), key=lambda x: (-1 * x.lowest_depth))
        return resolved_child_tails

    self.visualization_containers = parseDFTree(self.computation_tree)

