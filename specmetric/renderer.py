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

