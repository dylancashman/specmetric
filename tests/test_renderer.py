from specmetric.renderer import AltairRenderer
from specmetric.visualization_container import VisualizationContainer
from specmetric.computation_tree import ComputationNode
from altair import Chart

def helper_containers_from_specs(specs):
  vcs = []
  for spec in specs:
    fake_root_node = ComputationNode('fake', None, 'scalar')
    vc = VisualizationContainer(fake_root_node)
    vc.valid_chart = spec['valid_chart']
    vc.encodings = spec['encodings']
    vcs.append(vc)
  return vcs

def test_bar_chart_diff():
  specs = [
    {
      'valid_chart': 'bar_chart_diff',
      'encodings': {
        "a": {
          "mark": "line",
          "channels": "scalar-location"
        },
        "b": {
          "mark": "line",
          "channels": "scalar-location"
        }
      }
    }
  ]
  data_dict = {
    'a': 5,
    'b': 7.0
  }
  vc = helper_containers_from_specs(specs)
  r = AltairRenderer(vc, data_dict)
  chart = r.convert_to_charts()
  
  assert chart.mark == 'bar'
  # assert labels are a and b

def test_bar_chart_diff_squares():
  specs = [
    {
      'valid_chart': 'bar_chart_diff',
      'encodings': {
        "a": {
          "mark": "square",
          "channels": "vector-location"
        },
        "b": {
          "mark": "square",
          "channels": "vector-location"
        }
      }
    }
  ]
  data_dict = {
    'a': [1, 4, 2, 5, 6, 9, 5, 20],
    'b': [3, 1, 12]
  }
  vc = helper_containers_from_specs(specs)
  r = AltairRenderer(vc, data_dict)
  chart = r.convert_to_charts()
  
  print(chart)
  assert chart.mark == 'rect'
  # assert labels are a and b

def test_multiple_bar_chart():
  specs = [
    {
      'valid_chart': 'bar_chart_diff',
      'encodings': {
        "a": {
          "mark": "line",
          "channels": "scalar-location"
        },
        "b": {
          "mark": "line",
          "channels": "scalar-location"
        }

      }
    },
    {
      'valid_chart': 'bar_chart_diff',
      'encodings': {
        "c": {
          "mark": "line",
          "channels": "scalar-location"
        },
        "b": {
          "mark": "line",
          "channels": "scalar-location"
        }

      }
    }
  ]
  data_dict = {
    'a': 5,
    'b': 7.0,
    'c': 100
  }
  vc = helper_containers_from_specs(specs)
  r = AltairRenderer(vc, data_dict)
  chart = r.convert_to_charts()
  
  chart = charts[1]
  assert chart.mark == 'bar'

def test_bar_chart_comp():
  specs = [
    {
      'valid_chart': 'bar_chart_comp',
      'encodings': {
        "a": {
          "mark": "line",
          "channels": "scalar-location"
        },
        "b": {
          "mark": "line",
          "channels": "scalar-location"
        }

      }
    }
  ]
  data_dict = {
    'a': 5,
    'b': 7.0
  }
  vc = helper_containers_from_specs(specs)
  r = AltairRenderer(vc, data_dict)
  chart = r.convert_to_charts()
  
  assert chart.mark == 'bar'
  # assert labels are a and b

def test_scatter_y_equals_x():
  specs = [
    {
      'valid_chart': 'scatter_y_equals_x',
      'encodings': {
        "a": {
          "mark": "point",
          "channels": "vector-location",
          "preference": 'x'
        },
        "b": {
          "mark": "point",
          "channels": "vector-location",
          "preference": 'y'
        },
        "bline": {
          "mark": "line",
          "channels": "vector-location"
        },
        "bsquare": {
          "mark": "square",
          "channels": "vector-location"
        }

      }
    }
  ]
  data_dict = {
    'a': [1, 1, 3, 1, 2],
    'b': [2, 1, 0, 1, -45],
    'bline': [1,2,3,4,5],
    'bsquare': [3,2,3,5,6]
  }
  vc = helper_containers_from_specs(specs)
  r = AltairRenderer(vc, data_dict)
  chart = r.convert_to_charts()
  
  assert chart.mark == 'point'

  # chart = charts[1]
  # assert chart.mark == 'line'

  # chart = charts[2]
  # assert chart.mark == 'rect'

def test_spacefilling():
  specs = [
    {
      'valid_chart': 'spacefilling',
      'encodings': {
        "a": {
          "mark": "square",
          "channels": "vector-location"
        }

      }
    }
  ]
  data_dict = {
    'a': [1, 1, 3, 1, 2]
  }
  vc = helper_containers_from_specs(specs)
  r = AltairRenderer(vc, data_dict)
  chart = r.convert_to_charts()
  
  assert chart.mark == 'rect'



