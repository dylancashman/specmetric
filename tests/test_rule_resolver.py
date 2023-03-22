from specmetric.rule_resolver import VisualizationRule

def test_resolve_parent_type():
	preferences = {}
	parent_type = 'vector'
	rule = VisualizationRule(preferences, parent_type)

	rule.resolve_parent_type()
	assert(rule.valid)