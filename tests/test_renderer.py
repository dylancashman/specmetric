from specmetric.renderer import AltairRenderer
from altair import Chart

def test_convert_to_charts():
	specs = {}
	data_dict = {}
	r = AltairRenderer(specs, data_dict)
	charts = r.convert_to_charts(specs, data_dict)
	assert len(charts) > 0
	assert charts[0].isinstance(Chart)