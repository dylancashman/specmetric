import pandas as pd
import altair as alt
from specmetric.position_calculators.squarifier import squarify_within_bar

class AltairRenderer:
  """
  AltairRenderer takes in a list of resolved specifications and produces 
  a sequence of charts that should be cross-linked

  specifications should also include the data needed to render the visualization

  In future version, specs can be incomplete specifications, and filled in by
  constraint solver like draco.  For now, we allow a certain number of charts
  and process any links within the charts.  

  Allowed charts

    - scatter_y_equals_x
      - defines two primary attributes on x and y axis
      - marks correspond to input vector, using those two axes
      - marks can be imbued with additional encodings, like lines or squares
    - bar_chart_comp
      - chart with two bars comparing two values
      - y axis is the value of the two bars
      - x axis is categorical, "new" data attribute defined on inputs
    - bar_chart_diff
      - chart with two bars comparing two values
      - y axis is the value of the two bars
      - x axis is categorical, "new" data attribute defined on inputs
      - Something else besides comp?  Let's see
    - spacefilling
      - chart with single bar
      - defines single primary attribute

  Uses consistent scales across all visualizations, if possible
  Also tries to use unique IDs for post-hoc cross linking
  """

  def __init__(self, resolved_specifications, data_dict):
    self.resolved_specifications = resolved_specifications
    self.data_dict = data_dict
    self.convert_to_charts()

  def convert_to_charts(self):
    charts = []
    for spec in self.resolved_specifications:
      # Render altair chart, but make sure that we have all needed scales
      # defined, including colors, since they will be shared.
      charts.append(self.build_chart(spec))

    return charts

  def build_chart(self, spec):
    if spec.valid_chart == 'bar_chart_diff':
      scalar_data = pd.DataFrame()
      vector_data = pd.DataFrame()
      chart_data = pd.DataFrame()
      # print("spec.encodings is ", spec.encodings)
      for attr, encodings in spec.encodings.items():
        if 'scalar' in encodings['channels']:
          scalar_data[attr] = self.data_dict[attr]

        if 'vector' in encodings['channels']:
          vector_data[attr] = self.data_dict[attr]

      charts = []
      # Then, need to calculate any additional attributes
      if (scalar_data.shape[0] > 0):
        # we put all scalar data into a single column
        chart_data['scalar_values'] = scalar_data.iloc[0].values
        # and add a second column with the names of the scalars
        # so that they can be colored categorically
        chart_data['scalar_names'] = scalar_data.columns.values

        # # first, draw the scalar bars

        charts.append(alt.Chart(scalar_data).mark_bar().encode(
          x='scalar_names',
          y='scalar_values'
          ))

      total_height = 400.0
      # then, draw any vector encodings
      max_total = vector_data.sum(axis=1).maximum()

      if (vector_data.shape[0] > 0):
        # We have a spacefilling visualization
        # we use a square packing algorithm
        # we have to calculate the offsets, however.
        num_bars = vector_data.shape[1]
        bar_width = 50
        bar_padding = 30
        for i in np.range(num_bars):
          offset = ((i + 1) * padding) + (i * bar_width)
          values = vector_data[[i]].values
          total = np.sum(values)
          bar_height = (total / max_total) * total_height
          squares = squarify_within_bar(vector_data.index, values, bar_width, bar_height, pad=True):
          
