import pandas as pd

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

  def calculate_spacefilling_coords(self):
    # Need to check for offset
    # offset: tied-{{var_name}}
    # The var_name should correspond to a particular mark with an x and a y.
    # The offset gets applied by being added to each of the x,y,x2,y2 of 
    # spacefilling coords
    pass
