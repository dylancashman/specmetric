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
    - mean_chart
      - Shows each value in order of size
      - highlights mean and median
    - dist_chart
      - Shows distribution of values, either numeric or categorical

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
        result_chart = result_chart | curr
      else:
        result_chart = curr

    return result_chart

  def build_chart(self, spec, categorical_color_scale, crosslinker):
    charts = []
    scalar_data = OrderedDict()
    vector_data = OrderedDict()
    skipped_data = OrderedDict()
    total_height = 400.0
    total_width = 400.0
    title = ''

    for attr, encodings in spec.encodings.items():
      if 'scalar' in encodings['channels']:
        scalar_data[attr] = self.data_dict[attr]

      if 'vector' in encodings['channels']:
        vector_data[attr] = self.data_dict[attr]

      if 'skip' in encodings:
        skipped_data[attr] = self.data_dict[attr]

    scalar_keys = list(scalar_data.keys())
    vector_keys = list(vector_data.keys())
    skipped_keys = list(skipped_data.keys())

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
        charts.append(ratio_plot)
    elif (spec.valid_chart == 'dist_chart'):
      for attr in vector_keys:
        values = self.data_dict[attr];
        # We want to show distribution of values
        values_df = pd.DataFrame(data={'val': values})
        dist_chart = alt.Chart(values_df).mark_bar().encode(
          alt.X("val", bin=True),
          y='count()',
        ).properties(width=total_width, height=total_height, title=title
              ).add_selection(crosslinker)
        charts.append(dist_chart)

    elif (spec.valid_chart == 'mean_chart'):
      if (len(vector_keys) > 0):
        # We have a mean visualization
        # We lay out the marks on an x axis in order of their value
        # and also draw the mean, annotated
        for attr in vector_keys:
          values = self.data_dict[attr]
          if 'ids' in self.data_dict:
            ids = self.data_dict['ids']
          else:
            ids = range(0,len(values))

          mean_value = np.mean(values)
          median_value = np.median(values)

          values_df = pd.DataFrame(data={'val': values, 'is_mean': False, 'is_median': False}, index=ids)
          for input_var in self.input_vars:
            values_df[input_var] = self.data_dict[input_var]

          for skipped_var in skipped_keys:
            values_df[skipped_var] = self.data_dict[skipped_var]

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

          values_df.loc[len(values_df)] = mean_row
          values_df.loc[len(values_df)] = median_row

          values_df = values_df.sort_values(by='val')
          values_df['id'] = values_df.index.values
          values_df = values_df.reset_index(drop=True)
          values_df['x'] = values_df.index.values # should give 0-indexed counter

          tooltip_columns = sorted(list(set(values_df.columns.values) & set(self.input_vars + ['id'])))

          mean_x_location = values_df[values_df['is_mean']].iloc[0].x
          median_x_location = values_df[values_df['is_median']].iloc[0].x          
          values_df['color'] = attr
          values_df['color'] = values_df.apply((lambda x: 'mean' if x.is_mean else x.color), axis=1)
          values_df['color'] = values_df.apply((lambda x: 'median' if x.is_median else x.color), axis=1)

          mark = spec.encodings[attr]['mark'] or 'square'
          if mark == 'line' and ((len(vector_keys) < 2) or ('skip' not in spec.encodings[attr])):
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
              # color=alt.Color('color', scale=categorical_color_scale, legend=None),
            ).properties(width=total_width, height=total_height, title=title
            # )
            ).add_selection(crosslinker)
            charts.append(line_plot)

          if mark == 'bar-compare':
            # We need to get the 'skip' attributes (bars) and place 
            # them according to this attribute

            # we draw small bars at each point
            bar_width = 0.25
            ratio_bar_dataframes = []
            for i, bar_type in enumerate(skipped_keys):
              ratio_bar_data = pd.DataFrame()
              ratio_bar_data['x-ratio'] = values_df['x'] + (i*bar_width)
              ratio_bar_data['y-ratio'] = 0
              ratio_bar_data['x2-ratio'] = values_df['x'] + ((i+1)*bar_width)
              ratio_bar_data['y2-ratio'] = values_df[bar_type]
              ratio_bar_data['color-ratio'] = bar_type
              ratio_bar_data['id'] = values_df['id']
              ratio_bar_dataframes.append(ratio_bar_data)

            ratio_bar_data = pd.concat(ratio_bar_dataframes)
            bar_plot = alt.Chart(ratio_bar_data).mark_rect(opacity=0.4).encode(
              x=alt.X('x-ratio', axis=alt.Axis(title='', labels=False)),
              y=alt.Y('y-ratio', axis=alt.Axis(title="Ratio of {} to {}".format(skipped_keys[0], skipped_keys[1]), labels=False), scale=self.vector_scale),
              x2=alt.X2('x2-ratio'),
              y2=alt.Y2('y2-ratio'),
              # color=alt.Color('color-ratio', scale=categorical_color_scale, legend=None),
              color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color-ratio', scale=categorical_color_scale, legend=None)), 
            ).add_selection(crosslinker)
            # )
            mean_x_location = values_df[values_df['is_mean']].iloc[0].x
            median_x_location = values_df[values_df['is_median']].iloc[0].x

            charts.append(bar_plot)

          if mark == 'square':
            # We do a little hack to keep the squares the right size, but on a single chart
            values_df['sqrtval'] = np.sqrt(values_df['val'])
            padding=3
            values_df['squarex'] = 0
            for i in range(1, len(values_df)):
              values_df.loc[i, 'squarex'] = values_df.loc[i-1, 'squarex'] + values_df.loc[i-1, 'sqrtval'] + padding

            values_df['y'] = 0
            values_df['x2'] = values_df['squarex'] + values_df['sqrtval']
            values_df['y2'] = np.sqrt(values_df['val'])

            title = "Distributions of {}".format(attr)
            line_plot = alt.Chart(values_df).mark_rect(opacity=0.2).encode(
              x=alt.X('squarex', scale=self.vector_scale, axis=alt.Axis(title='', labels=False)),
              y=alt.Y('y', scale=self.vector_scale, axis=alt.Axis(title=attr)),
              x2=alt.X2('x2'),
              y2=alt.Y2('y2'),
              tooltip=tooltip_columns,
              color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color', scale=categorical_color_scale, legend=None)),
            ).properties(height=total_height, title=title).add_selection(crosslinker)
            charts.append(line_plot)
            mean_x_location = values_df[values_df['is_mean']].iloc[0].squarex
            median_x_location = values_df[values_df['is_median']].iloc[0].squarex

          # whatever mark, we put dotted annotations of where the mean and median are
          mean_line_data = pd.DataFrame(data={
            'x': [mean_x_location - 0.1, mean_x_location - 0.1], 
            'y': [0, total_height],
            'color': ['mean', 'mean']})
          mean_line = alt.Chart(mean_line_data).mark_line(strokeDash=[5,3], opacity=0.5, strokeWidth=2).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.Color('color', scale=categorical_color_scale, legend=None)
          )
          mean_text = alt.Chart(mean_line_data).mark_text(
            align='left',
            baseline='middle',
            fontSize=20,
            dx=7
          ).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.Color('color', scale=categorical_color_scale, legend=None),
            text=alt.value("mean = {0:.2f}".format(mean_value))
          ).transform_filter(
            (datum.y > 0)
          )
          if (len(vector_keys) == 1 or ('skip' not in spec.encodings[attr])): 
            charts.append(mean_line)
            charts.append(mean_text)

          median_line_data = pd.DataFrame(data={
            'x': [median_x_location + 0.1, median_x_location + 0.1], 
            'y': [0, total_height * 0.8],
            'color': ['median', 'median']})
          median_line = alt.Chart(median_line_data).mark_line(strokeDash=[5,3], opacity=0.5, strokeWidth=2).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.Color('color', scale=categorical_color_scale, legend=None)
          )
          median_text = alt.Chart(median_line_data).mark_text(
            align='left',
            baseline='middle',
            fontSize=20,
            dx=7
          ).encode(
            x=alt.X('x'),
            y=alt.Y('y'),
            color=alt.Color('color', scale=categorical_color_scale, legend=None),
            text=alt.value("median = {0:.2f}".format(median_value))
          ).transform_filter(
            (datum.y > 0)
          )
          if (len(vector_keys) == 1 or ('skip' not in spec.encodings[attr])):
            charts.append(median_line)
            charts.append(median_text)

          # Now, if there is a scalar key, it means that we have a sqrt
          if len(scalar_keys) > 0:
            scalar_key = scalar_keys[0]
            sqrt_val = np.sqrt(mean_value)
            # we draw a line on the mean chart
            mean_sqrt_data = pd.DataFrame(data={
              'x': [mean_x_location - 0.1, mean_x_location - 0.1 + sqrt_val], 
              'y': [sqrt_val, sqrt_val],
              'color': ['sqrt', 'sqrt']})
            mean_sqrt_line = alt.Chart(mean_sqrt_data).mark_line(opacity=1.0, strokeWidth=5).encode(
              x=alt.X('x'),
              y=alt.Y('y'),
              color=alt.Color('color', scale=categorical_color_scale, legend=None)
            )
            mean_sqrt_text = alt.Chart(mean_sqrt_data).mark_text(
              align='left',
              baseline='middle',
              fontSize=20,
              dx=7
            ).encode(
              x=alt.X('x'),
              y=alt.Y('y'),
              color=alt.Color('color', scale=categorical_color_scale, legend=None),
              text=alt.value(scalar_key + " = {0:.2f}".format(sqrt_val))
            ).transform_filter(
              (datum.x > mean_x_location)
            )
            charts.append(mean_sqrt_line)
            charts.append(mean_sqrt_text)

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
          if 'ids' in self.data_dict:
            ids = self.data_dict['ids']
          else:
            ids = range(0,len(values))
          squares = squarify_within_bar(ids, values, bar_width, bar_height, pad=True)

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
        charts.append(ratio_plot)
    elif spec.valid_chart == 'scatter_y_equals_x':
      # Then, need to calculate any additional attributes
      if (len(vector_keys) > 0):
        # These are the scatters
        vector_encodings = list(vector_data.keys())
        num_encodings = len(vector_encodings)

        scatter_data = pd.DataFrame()
        dot_attrs = []
        line_attrs = []
        square_attrs = []
        bar_attrs = []
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
              if len(vector_keys) > 1 and 'skip' in encodings:
                scatter_data['color'] = attr # we keep the color but
                scatter_data[attr] = self.data_dict[attr]
                bar_attrs.append(attr)
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

          if (encodings['mark'] == 'bar-compare'):
            bar_attrs.append(attr)
            scatter_data[attr] = self.data_dict[attr]
            scatter_data['color-'+attr] = attr

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
          # color=alt.Color('color', scale=categorical_color_scale, legend=None),
          tooltip=tooltip_columns
        ).properties(width=total_width, height=total_height, title=title)
        charts.append(dot_plot)
        # realign the axes
        max_pixel = scatter_data[['x', 'y']].max().max() * 1.1


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
            # color=alt.Color('color', scale=categorical_color_scale, legend=None),
          ).properties(width=total_width, height=total_height, title=title).add_selection(crosslinker)
          charts.append(square_plot)
          # realign the axes
          max_pixel = scatter_data[['x', 'y', 'squarex2', 'squarey2']].max().max() * 1.1
          # self.vector_scale.domain = [0,max_pixel]

        elif ('linediff' in scatter_data.columns.values) and (len(bar_attrs) == 0):
        # elif ('linediff' in scatter_data.columns.values):
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
          charts.append(line_plot)
          # realign the axes
          max_pixel = scatter_data[['x', 'y', 'liney2']].max().max() * 1.1
          # self.vector_scale.domain = [0,max_pixel]

        if len(bar_attrs) > 0:
          # we draw small bars at each point
          bar_width = 5
          ratio_bar_dataframes = []
          for i, bar_type in enumerate(bar_attrs):
            ratio_bar_data = pd.DataFrame()
            ratio_bar_data['x-ratio'] = scatter_data['x'] + (i*bar_width)
            ratio_bar_data['y-ratio'] = scatter_data['y']
            ratio_bar_data['x2-ratio'] = scatter_data['x'] + ((i+1)*bar_width)
            ratio_bar_data['y2-ratio'] = scatter_data['y'] - scatter_data[bar_type]
            ratio_bar_data['color-ratio'] = bar_type
            ratio_bar_data['id'] = self.data_dict['ids']
            ratio_bar_dataframes.append(ratio_bar_data)

          ratio_bar_data = pd.concat(ratio_bar_dataframes)
          bar_plot = alt.Chart(ratio_bar_data).mark_rect(opacity=0.4).encode(
            x=alt.X('x-ratio', scale=self.vector_scale),
            y=alt.Y('y-ratio', scale=self.vector_scale),
            x2=alt.X2('x2-ratio'),
            y2=alt.Y2('y2-ratio'),
            # color=alt.Color('color-ratio', scale=categorical_color_scale, legend=None),
            color=alt.condition(crosslinker, alt.value('yellow'), alt.Color('color-ratio', scale=categorical_color_scale, legend=None)), 
          ).add_selection(crosslinker)
          # )
          charts.append(bar_plot)

      y_equals_x_data = pd.DataFrame(data={'x': self.vector_scale.domain, 'y': self.vector_scale.domain})
      y_equals_x_chart = alt.Chart(y_equals_x_data).mark_line().encode(
        x=alt.X('x'),
        y=alt.Y('y')
      )
      charts.append(y_equals_x_chart)

    return charts


