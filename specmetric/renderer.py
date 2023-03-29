import pandas as pd
import numpy as np
import altair as alt
from specmetric.position_calculators.squarifier import squarify_within_bar
from collections import OrderedDict

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
      charts = charts + self.build_chart(spec)

    return charts

  def build_chart(self, spec):
    charts = []
    scalar_data = OrderedDict()
    vector_data = OrderedDict()

    for attr, encodings in spec.encodings.items():
      if 'scalar' in encodings['channels']:
        scalar_data[attr] = self.data_dict[attr]

      if 'vector' in encodings['channels']:
        vector_data[attr] = self.data_dict[attr]

    if (spec.valid_chart == 'bar_chart_diff') or (spec.valid_chart == 'bar_chart_comp'):
      # Then, need to calculate any additional attributes
      if (len(scalar_data.keys()) > 0):
        chart_data = pd.DataFrame()
        # we put all scalar data into a single column
        chart_data['scalar_values'] = list(scalar_data.values())
        # and add a second column with the names of the scalars
        # so that they can be colored categorically
        chart_data['scalar_names'] = list(scalar_data.keys())

        # # first, draw the scalar bars
        chart = alt.Chart(scalar_data).mark_bar()

        chart.encode(
          x='scalar_names',
          y='scalar_values'
        )
        charts.append(chart)

      if (len(vector_data.keys()) > 0):
        total_height = 400.0
        # then, draw any vector encodings
        sums = [np.sum(d) for (_,d) in vector_data.items()]
        max_total = max(sums)

        colors=['red', 'blue', 'green', 'black', 'orange', 'pink', 'purple', 'gray']
        # We have a spacefilling visualization
        # we use a square packing algorithm
        # we have to calculate the offsets, however.
        num_bars = len(vector_data.keys())
        original_column_names = list(vector_data.keys())
        bar_width = 50
        bar_padding = 30
        total_bar_data = []
        for i in np.arange(num_bars):
          colname = original_column_names[i]
          offset = ((i + 1) * bar_padding) + (i * bar_width)

          values = vector_data[colname]
          total = np.sum(values)
          bar_height = (total / max_total) * total_height
          squares = squarify_within_bar(values, bar_width, bar_height, pad=True)
          
          bar_data = pd.DataFrame()
          bar_data['__x__'] = squares['x'] + offset
          bar_data['__x2__'] = squares['x'] + offset + squares['dx']
          bar_data['__y__'] = squares['y']
          bar_data['__y2__'] = squares['y'] + squares['dy']
          bar_data['color'] = colors[i]
          total_bar_data.append(bar_data)

        total_bar_df = pd.concat(total_bar_data)
        ratio_plot = alt.Chart(total_bar_df).mark_rect()
        ratio_plot.encode(
          x=alt.X('__x__'),
          y=alt.Y('__y__'),
          x2=alt.X2('__x2__'),
          y2=alt.Y2('__y2__'),
          color=alt.Color('color', scale=None)
        )
        charts.append(ratio_plot)
    elif (spec.valid_chart == 'spacefilling'):

      if (len(vector_data.keys()) > 0):
        total_height = 400.0
        # then, draw any vector encodings
        sums = [np.sum(d) for (_,d) in vector_data.items()]
        max_total = max(sums)

        colors=['red', 'blue', 'green', 'black', 'orange', 'pink', 'purple', 'gray']
        # We have a spacefilling visualization
        # we use a square packing algorithm
        # we have to calculate the offsets, however.
        num_bars = len(vector_data.keys())
        original_column_names = list(vector_data.keys())
        bar_width = 50
        bar_padding = 30
        total_bar_data = []
        for i in np.arange(num_bars):
          colname = original_column_names[i]
          offset = ((i + 1) * bar_padding) + (i * bar_width)

          values = vector_data[colname]
          total = np.sum(values)
          bar_height = (total / max_total) * total_height
          squares = squarify_within_bar(values, bar_width, bar_height, pad=True)
          
          bar_data = pd.DataFrame()
          bar_data['__x__'] = squares['x'] + offset
          bar_data['__x2__'] = squares['x'] + offset + squares['dx']
          bar_data['__y__'] = squares['y']
          bar_data['__y2__'] = squares['y'] + squares['dy']
          bar_data['color'] = colors[i]
          total_bar_data.append(bar_data)

        total_bar_df = pd.concat(total_bar_data)
        ratio_plot = alt.Chart(total_bar_df).mark_rect()
        ratio_plot.encode(
          x=alt.X('__x__'),
          y=alt.Y('__y__'),
          x2=alt.X2('__x2__'),
          y2=alt.Y2('__y2__'),
          color=alt.Color('color', scale=None)
        )
        charts.append(ratio_plot)
    elif spec.valid_chart == 'scatter_y_equals_x':
      # Then, need to calculate any additional attributes
      if (len(scalar_data.keys()) > 0):
        # chart_data = pd.DataFrame()
        # # we put all scalar data into a single column
        # chart_data['scalar_values'] = list(scalar_data.values())
        # # and add a second column with the names of the scalars
        # # so that they can be colored categorically
        # chart_data['scalar_names'] = list(scalar_data.keys())

        # # first, draw the scalar bars
        # chart = alt.Chart(scalar_data).mark_bar()

        # chart.encode(
        #   x='scalar_names',
        #   y='scalar_values'
        # )
        # charts.append(chart)
        # not sure what we do with the scalar encodings.  But it happens here.
        # Basically, we should have a tied input (for things like the y=x line or
        # the y=ybar line)
        pass

      if (len(vector_data.keys()) > 0):
        # These are the scatters
        vector_encodings = list(vector_data.keys())
        num_encodings = len(vector_encodings)

        scatter_data = pd.DataFrame()
        print("spec is ", spec.pp())
        for attr, encodings in spec.encodings.items():
          if attr in vector_encodings:
            # First, check for points
            if (encodings['mark'] == 'point') and (encodings['preference'] == 'x'):
              scatter_data['x'] = self.data_dict[attr]
            elif (encodings['mark'] == 'point') and (encodings['preference'] == 'y'):
              scatter_data['y'] = self.data_dict[attr]
            elif (encodings['mark'] == 'line'):
              scatter_data['linediff'] = self.data_dict[attr]
            elif (encodings['mark'] == 'square'):
              scatter_data['squarediff'] = self.data_dict[attr]

        # Then, we build the charts
        # First, the dots
        dot_plot = alt.Chart(scatter_data).mark_point()
        dot_plot.encode(
          x=alt.X('x'),
          y=alt.Y('y')
        )
        charts.append(dot_plot)

        # Then, lines if they exist
        if 'linediff' in scatter_data.columns.values:
          scatter_data['liney2'] = scatter_data['y'] - scatter_data['linediff']
          line_plot = alt.Chart(scatter_data).mark_line()
          line_plot.encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            x2=alt.X2('x'),
            y2=alt.Y2('liney2') # The diff is always the second operand
          )
          charts.append(line_plot)

        # Then, squares if they exist
        if 'squarediff' in scatter_data.columns.values:
          scatter_data['squarex2'] = scatter_data['x'] + scatter_data['squarediff']
          scatter_data['squarey2'] = scatter_data['y'] - scatter_data['squarediff']
          square_plot = alt.Chart(scatter_data).mark_rect()
          square_plot.encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            x2=alt.X2('squarex2'),
            y2=alt.Y2('squarey2') 
          )
          charts.append(square_plot)

    return charts


