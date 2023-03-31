import pandas as pd
import numpy as np
import altair as alt
from altair import datum
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

  def __init__(self, resolved_specifications, data_dict, input_vars=[]):
    self.resolved_specifications = resolved_specifications
    self.data_dict = data_dict
    self.input_vars = input_vars
    # self.max_vector_axis = 400 # refactor
    self.vector_scale = alt.Scale(domain=[0,500])

  def convert_to_charts(self):
    charts = []
    categorical_color_scale = alt.Scale(scheme='category10')
    crosslinker = alt.selection_single(fields=['id'], on='mouseover', empty='none')

    for spec in self.resolved_specifications:
      # Render altair chart, but make sure that we have all needed scales
      # defined, including colors, since they will be shared.
      charts.append(self.build_chart(spec, categorical_color_scale, crosslinker))

    return self.flatten_charts(charts)

  def flatten_charts(self, charts):
    # add (+) together second level charts, and union (|) the first level results
    result_chart = None
    for cs in charts:
      curr = None
      for c in cs:
        if curr:
          curr = curr + c
        else:
          curr = c

      if result_chart:
        print("result_chart is ", result_chart, " and curr is ", curr)
        result_chart = result_chart | curr
      else:
        result_chart = curr

    return result_chart

  def build_chart(self, spec, categorical_color_scale, crosslinker):
    charts = []
    scalar_data = OrderedDict()
    vector_data = OrderedDict()
    total_height = 400.0
    total_width = 400.0
    title = ''

    for attr, encodings in spec.encodings.items():
      if 'scalar' in encodings['channels']:
        scalar_data[attr] = self.data_dict[attr]

      if 'vector' in encodings['channels']:
        vector_data[attr] = self.data_dict[attr]

    scalar_keys = list(scalar_data.keys())
    vector_keys = list(vector_data.keys())

    if (spec.valid_chart == 'bar_chart_diff') or (spec.valid_chart == 'bar_chart_comp'):
      # Then, need to calculate any additional attributes
      bar_width = 150
      bar_padding = 50

      # First, make scale
      if (len(scalar_data.keys()) > 0):
        chart_data = pd.DataFrame()
        # we put all scalar data into a single column
        chart_data['scalar_values'] = list(scalar_data.values())
        # and add a second column with the names of the scalars
        # so that they can be colored categorically
        chart_data['scalar_names'] = list(scalar_data.keys())
        opacity = 1.0
        if len(vector_keys) > 0:
          # We are doing spacefilling, so we hide the bars
          # but keep the labels
          opacity = 0.1

        # # first, draw the scalar bars
        if spec.valid_chart == 'bar_chart_diff':
          title = "{} - {}".format(scalar_keys[0], scalar_keys[1])
        else:
          title = "{} / {}".format(scalar_keys[0], scalar_keys[1])
        chart = alt.Chart(chart_data).mark_bar(opacity=opacity, size=bar_width).encode(
          x=alt.X('scalar_names', axis=alt.Axis(title='')),
          y=alt.Y('scalar_values', axis=alt.Axis(title='magnitude'))
        ).properties(width=total_width, height=total_height, title=title)
        print("bar chart plot is ", chart)
        charts.append(chart)

      if (len(vector_data.keys()) > 0):
        # If we're going to do spacefilling, then we are going to replace the 
        # existing bars with spacefilling.  So we set their opacity to 0.

        opacity=0.2
        # then, draw any vector encodings
        sums = [np.sum(d) for (_,d) in vector_data.items()]
        max_total = max(sums)

        # We have a spacefilling visualization
        # we use a square packing algorithm
        # we have to calculate the offsets, however.
        num_bars = len(vector_data.keys())
        original_column_names = list(vector_data.keys())
        total_bar_data = []
        for i in np.arange(num_bars):
          colname = original_column_names[i]
          offset = ((i + 0.5) * bar_padding) + (i * bar_width)

          values = vector_data[colname]
          total = np.sum(values)

          # We actually want to pass in the height and width 
          # in the bar chart's target encoding
          # The bar width is a little harder to reason about.
          # bar_height = (total / max_total) * total_height
          # However, we need to normalize things or else the
          # padding calculations break
          modulated_bar_height = 100
          squares = squarify_within_bar(self.data_dict['ids'], values, bar_width, modulated_bar_height, pad=True)
          height_multiplier = total / modulated_bar_height
          
          bar_data = pd.DataFrame()
          bar_data['__x__'] = squares['x'] + offset
          bar_data['__x2__'] = squares['x'] + offset + squares['dx']
          bar_data['__y__'] = squares['y'] * height_multiplier
          bar_data['__y2__'] = (squares['y'] + squares['dy']) * height_multiplier
          bar_data['color'] = colname
          bar_data['part of'] = scalar_keys[i]
          bar_data['id'] = squares.index.values
          for input_var in self.input_vars:
            bar_data[input_var] = self.data_dict[input_var]

          total_bar_data.append(bar_data)

        total_bar_df = pd.concat(total_bar_data)

        title = "Comparison of sum of {} and {}".format(vector_keys[0], vector_keys[1])
        tooltip_columns = sorted(list(set(total_bar_df.columns.values) & set(self.input_vars + ['id', 'part of'])))
        ratio_plot = alt.Chart(total_bar_df).mark_rect(opacity=0.2).encode(
          x=alt.X('__x__', axis=alt.Axis(title='', labels=False), scale=alt.Scale(domain=[0,total_width])),
          y=alt.Y('__y__', axis=alt.Axis(title='magnitude')),
          x2=alt.X2('__x2__'),
          y2=alt.Y2('__y2__'),
          color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=categorical_color_scale, legend=None)),
          tooltip=tooltip_columns
        ).properties(width=total_width, height=total_height, title=title).add_selection(crosslinker)
        print("bar chart spacefilling plot is ", ratio_plot)
        charts.append(ratio_plot)
    elif (spec.valid_chart == 'mean_chart'):
      if (len(vector_data.keys()) > 0):
        # We have a mean visualization
        # We lay out the marks on an x axis in order of their value
        # and also draw the mean, annotated
        for attr, data in vector_data.items():
          values = self.data_dict[attr]
          ids = self.data_dict['ids']
          mean_value = np.mean(values)
          median_value = np.median(values)

          values_df = pd.DataFrame(data={'val': values, 'is_mean': False, 'is_median': False}, index=ids)
          for input_var in self.input_vars:
            values_df[input_var] = self.data_dict[input_var]

          # we add in the mean value with id -1
          # we add in the median value with id -2
          # values.append(mean_value)
          # ids.append(-1)
          # values = np.append(mean_value, values)
          # ids = np.append(-1, ids)
          mean_row = []
          median_row = []
          for col in values_df.columns.values:
            if col == 'val':
              mean_row.append(mean_value)
              median_row.append(median_value)
            elif col == 'is_mean':
              mean_row.append(True)
              median_row.append(False)
            elif col == 'is_median':
              mean_row.append(False)
              median_row.append(True)
            else:
              mean_row.append(-1)
              median_row.append(-2)

          # added = pd.DataFrame([mean_row, median_row], columns=values_df.columns)
          # values_df = values_df.append(added)
          values_df.loc[len(values_df)] = mean_row
          values_df.loc[len(values_df)] = median_row
          # we add in the median value with id -2
          # values.append(median_value)
          # ids.append(-2)
          # values = np.append(median_value, values)
          # ids = np.append(-2, ids)

          values_df = values_df.sort_values(by='val')
          values_df['id'] = values_df.index.values
          values_df = values_df.reset_index(drop=True)

          # mean_df = pd.DataFrame(data={'val': values_series.values, 'id': values_series.index.values})
          # print(values_df) 
          values_df['x'] = values_df.index.values # should give 0-indexed counter
          # values_df['is_mean'] = values_df['id'] == -1
          # values_df['is_median'] = values_df['id'] == -2

          tooltip_columns = sorted(list(set(values_df.columns.values) & set(self.input_vars + ['id'])))

          mean_x_location = values_df[values_df['is_mean']].iloc[0].x
          median_x_location = values_df[values_df['is_median']].iloc[0].x
          values_df['color'] = attr

          mark = spec.encodings[attr]['mark']
          if mark == 'line':
            values_df['y'] = 0
            values_df['x2'] = values_df['x']
            values_df['y2'] = values_df['val']
            title = "Distributions of {}".format(attr)
            line_plot = alt.Chart(values_df).mark_line().encode(
              x=alt.X('x', axis=alt.Axis(title='', labels=False)),
              y=alt.Y('y', scale=self.vector_scale, axis=alt.Axis(title=attr)),
              x2=alt.X2('x2'),
              y2=alt.Y2('y2'),
              tooltip=tooltip_columns,
              color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=categorical_color_scale, legend=None)),
            ).properties(width=total_width, height=total_height, title=title).add_selection(crosslinker)
            print("line line plot is ", line_plot)
            charts.append(line_plot)

          if mark == 'square':
            values_df['y'] = 0
            values_df['x2'] = values_df['x'] + np.sqrt(values_df['val'])
            values_df['y2'] = np.sqrt(values_df['val'])
            title = "Distributions of {}".format(attr)
            line_plot = alt.Chart(values_df).mark_rect(opacity=0.2).encode(
              x=alt.X('x', axis=alt.Axis(title='', labels=False)),
              y=alt.Y('y', scale=self.vector_scale, axis=alt.Axis(title=attr)),
              x2=alt.X2('x2'),
              y2=alt.Y2('y2'),
              tooltip=tooltip_columns,
              # color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=categorical_color_scale, legend=None)),
            ).properties(width=total_width, height=total_height, title=title).add_selection(crosslinker)
            print("rect line plot is ", line_plot)
            charts.append(line_plot)

          # whatever mark, we put dotted annotations of where the mean and median are
          mean_line_data = pd.DataFrame(data={
            'x': [mean_x_location - 0.1, mean_x_location - 0.1], 
            'y': [0, total_height], 
            'x2': [mean_x_location, median_x_location],
            'y2': [total_height, total_height]})
          mean_line = alt.Chart(mean_line_data).mark_line(strokeDash=[5,3], opacity=0.5, strokeWidth=2).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.value('pink')
          )
          mean_text = alt.Chart(mean_line_data).mark_text(
            align='left',
            baseline='middle',
            fontSize=20,
            dx=7
          ).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.value('pink'),
            text=alt.value("mean = {0:.2f}".format(mean_value))
          ).transform_filter(
            (datum.y > 0)
          )
          charts.append(mean_line)
          charts.append(mean_text)

          median_line_data = pd.DataFrame(data={
            'x': [median_x_location + 0.1, median_x_location + 0.1], 
            'y': [0, total_height * 0.8], 
            'x2': [median_x_location, median_x_location],
            'y2': [total_height, total_height]})
          median_line = alt.Chart(median_line_data).mark_line(strokeDash=[5,3], opacity=0.5, strokeWidth=2).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.value('purple')
          )
          median_text = alt.Chart(median_line_data).mark_text(
            align='left',
            baseline='middle',
            fontSize=20,
            dx=7
          ).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.value('purple'),
            text=alt.value("median = {0:.2f}".format(median_value))
          ).transform_filter(
            (datum.y > 0)
          )
          # print("mean lines plot is ", mean_line)
          charts.append(median_line)
          charts.append(median_text)


# if (encodings['mark'] == 'point') and (encodings['preference'] == 'x'):
#               scatter_data['x'] = self.data_dict[attr]
#               dot_attrs.append(attr)
#               scatter_data['color'] = attr
#             elif (encodings['mark'] == 'point') and (encodings['preference'] == 'y'):
#               scatter_data['y'] = self.data_dict[attr]
#               dot_attrs.append(attr)
#               scatter_data['color'] = attr
#             elif (encodings['mark'] == 'line'):
#               scatter_data['linediff'] = self.data_dict[attr]
#               line_attrs.append(attr)
#               scatter_data['color'] = attr
#             elif (encodings['mark'] == 'square'):
#               scatter_data['squarediff'] = np.sqrt(self.data_dict[attr])
#               square_attrs.append(attr)
#               scatter_data['color'] = attr









    elif (spec.valid_chart == 'spacefilling'):

      if (len(vector_data.keys()) > 0):
        # then, draw any vector encodings
        sums = [np.sum(d) for (_,d) in vector_data.items()]
        max_total = max(sums)

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
          bar_data['color'] = colname
          total_bar_data.append(bar_data)

        total_bar_df = pd.concat(total_bar_data)
        ratio_plot = alt.Chart(total_bar_df).mark_rect(opacity=0.2).encode(
          x=alt.X('__x__'),
          y=alt.Y('__y__'),
          x2=alt.X2('__x2__'),
          y2=alt.Y2('__y2__'),
          color=alt.Color('color', scale=categorical_color_scale, legend=None)
        ).properties(width=total_width, height=total_height, title=title)
        print("spacefilling plot is ", ratio_plot)
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
        dot_attrs = []
        line_attrs = []
        square_attrs = []
        for attr, encodings in spec.encodings.items():
          if attr in vector_encodings:
            # First, check for points
            if (encodings['mark'] == 'point') and (encodings['preference'] == 'x'):
              scatter_data['x'] = self.data_dict[attr]
              dot_attrs.append(attr)
              scatter_data['color'] = attr
            elif (encodings['mark'] == 'point') and (encodings['preference'] == 'y'):
              scatter_data['y'] = self.data_dict[attr]
              dot_attrs.append(attr)
              scatter_data['color'] = attr
            elif (encodings['mark'] == 'line'):
              if 'skip' in encodings:
                scatter_data['color'] = attr # we keep the color but
                pass # we don't want to blow out other encodings
              else:
                scatter_data['linediff'] = self.data_dict[attr]
                line_attrs.append(attr)
                scatter_data['color'] = attr
            elif (encodings['mark'] == 'square'):
              if 'skip' in encodings:
                pass # we don't want to blow out other encodings
              else:
                scatter_data['squarediff'] = np.sqrt(self.data_dict[attr])
                square_attrs.append(attr)
                scatter_data['color'] = attr

        if 'ids' in self.data_dict:
          scatter_data['id'] = self.data_dict['ids']
        
        for input_var in self.input_vars:
          scatter_data[input_var] = self.data_dict[input_var]

        # Then, we build the charts
        # First, the dots
        title = "Comparison of {} and {}".format(dot_attrs[0], dot_attrs[1])
        tooltip_columns = sorted(list(set(scatter_data.columns.values) & set(self.input_vars + ['id'])))
        dot_plot = alt.Chart(scatter_data).mark_point().encode(
          x=alt.X('x', axis=alt.Axis(title=dot_attrs[0]), scale=self.vector_scale),
          y=alt.Y('y', axis=alt.Axis(title=dot_attrs[1]), scale=self.vector_scale),
          color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=categorical_color_scale, legend=None)),
          tooltip=tooltip_columns
        ).properties(width=total_width, height=total_height, title=title)
        print("dot plot is ", dot_plot)
        charts.append(dot_plot)
        # realign the axes
        max_pixel = scatter_data[['x', 'y']].max().max() * 1.1
        # self.vector_scale.domain = [0,max_pixel]
        # for chart in charts:
        #   chart.encoding.x.scale = alt.Scale(domain=[0,max_pixel])
        #   chart.encoding.y.scale = alt.Scale(domain=[0,max_pixel])


        # Then, squares if they exist, or lines if they exist and squares don't
        # Then, squares if they exist
        if 'squarediff' in scatter_data.columns.values:
          scatter_data['squarex2'] = scatter_data['x'] + scatter_data['squarediff']
          scatter_data['squarey2'] = scatter_data['y'] + scatter_data['squarediff']
          title = "Magnitudes of {}".format(square_attrs[0])
          square_plot = alt.Chart(scatter_data).mark_rect(opacity=0.2).encode(
            x=alt.X('x', axis=alt.Axis(title=dot_attrs[0]), scale=self.vector_scale),
            y=alt.Y('y', axis=alt.Axis(title=dot_attrs[1]), scale=self.vector_scale),
            x2=alt.X2('squarex2'),
            y2=alt.Y2('squarey2'),
            tooltip=tooltip_columns,
            color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=categorical_color_scale, legend=None)),
          ).properties(width=total_width, height=total_height, title=title).add_selection(crosslinker)
          print("square plot is ", square_plot)
          charts.append(square_plot)
          # realign the axes
          max_pixel = scatter_data[['x', 'y', 'squarex2', 'squarey2']].max().max() * 1.1
          # self.vector_scale.domain = [0,max_pixel]

        elif 'linediff' in scatter_data.columns.values:
          scatter_data['liney2'] = scatter_data['y'] + scatter_data['linediff']
          title = "Magnitudes of {}".format(line_attrs[0])
          line_plot = alt.Chart(scatter_data).mark_line().encode(
            x=alt.X('x', axis=alt.Axis(title=dot_attrs[0]), scale=self.vector_scale),
            y=alt.Y('y', axis=alt.Axis(title=dot_attrs[1]), scale=self.vector_scale),
            x2=alt.X2('x'),
            y2=alt.Y2('liney2'),
            tooltip=tooltip_columns,
            color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=categorical_color_scale, legend=None)), # The diff is always the second operand
          ).properties(width=total_width, height=total_height, title=title).add_selection(crosslinker)
          print("line plot is ", line_plot)
          charts.append(line_plot)
          # realign the axes
          max_pixel = scatter_data[['x', 'y', 'liney2']].max().max() * 1.1
          # self.vector_scale.domain = [0,max_pixel]


          #@todo - I can define a scale every time we have an input tied.  And the in chart gets the scale of its output, out chart gets the color of its input
        #   color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=None)),
        #   tooltip=tooltip_columns
        # ).properties(width=total_width, height=total_height, title=title).add_selection(crosslinker)


      y_equals_x_data = pd.DataFrame(data={'x': self.vector_scale.domain, 'y': self.vector_scale.domain})
      y_equals_x_chart = alt.Chart(y_equals_x_data).mark_line().encode(
        x=alt.X('x'),
        y=alt.Y('y')
      )
      print("yequalsx plot is ", y_equals_x_chart)
      charts.append(y_equals_x_chart)

    # # put all the charts together, since they should share axes
    # resulting_chart = None
    # for chart in charts:
    #   if resulting_chart == None:
    #     resulting_chart = chart
    #   else:
    #     resulting_chart = resulting_chart + chart

    # charts = [resulting_chart]


    return charts


