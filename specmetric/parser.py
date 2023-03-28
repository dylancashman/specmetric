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

  def resolve_containers(parent_node, visualization_container_list, compositions=_compositions, grammatical_expressions=_grammatical_expressions):
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
    # print("in resolve_containers, len(visualization_container_list) is ", len(visualization_container_list))
    # print("visualization_container_list is ", visualization_container_list)
    # print("the parent_node is ", parent_node)
    parent_container = VisualizationContainer(parent_node, compositions=compositions, grammatical_expressions=grammatical_expressions)
    while(len(visualization_container_list) > 0):
      child_container = visualization_container_list.pop()
      # print("here, child_container is ", child_container)
      # print("and its valid_chart is ", child_container.valid_chart)
      if child_container.parent_mergeable(parent_node):
        print("it was mergeable")
        child_container.merge_parent(parent_node)
        # The child container has invaded the parent container and taken over
        parent_container = child_container
      else:
        print("it was not mergeable")
        unmerged_child_containers.append(child_container)

    # print("at the end, the parent_container has chart", parent_container.valid_chart)
    # Need something that fixes encodings, i.e. scales, colors
    # Let's try it without that for now, and see what happens
    # Similarly let's forget about cross-linking for now and just get it working
    unmerged_child_containers.append(parent_container)
    print("len(unmerged_child_containers) is ", len(unmerged_child_containers))
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
        return [[VisualizationContainer(tree, compositions=self.compositions, grammatical_expressions=self.grammatical_expressions)]]
      else:
        # if we are not at a leaf, we should have >0 children
        child_container_heads = []
        resolved_child_tails = []
        for child_node in tree.children:
          child_containers = parse_node(child_node)

          # head gets judged against parent
          head_container = child_containers.pop()
          child_container_heads = child_container_heads + head_container

          # tail goes into the stack together
          resolved_child_tails = resolved_child_tails + child_containers

        # We resolve the current node and the n child containers, which will 
        # result in either 1 visualization container (child and tree were merged)
        # or m<=n+1 containers, meaning either/or the child containers were incompatible
        # with the tree node, so we had to start a new visualization container, or the
        # child containers were not mergeable so they had to stay as separate visualizations

        # Then, we return the previous visualizations, and the visualization containers from
        # resolve_containers
        # print("resolved_child_tails is ", resolved_child_tails)
        print("child_container_heads is ", child_container_heads)
        print("resolved_child_tails is ", resolved_child_tails)
        resolved_child_tails.append(ComputationTreeParser.resolve_containers(tree, child_container_heads, self.compositions, self.grammatical_expressions))
        print("resolved_child_tails is ", resolved_child_tails)
        return resolved_child_tails

    self.visualization_containers = parse_node(self.computation_tree)

