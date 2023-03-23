from specmetric.rule_resolver import VisualizationRule

def test_resolve_parent_type():
	additional_preferences = {}
	parent_type = 'vector_sum'
	child_type = 'vector'
	rule = VisualizationRule(additional_preferences, parent_type, child_type)

	rule.resolve_parent_type()
	assert(rule.valid == False)

	child_type = 'scalar'
	rule = VisualizationRule(additional_preferences, parent_type, child_type)
	rule.resolve_parent_type()
	assert(rule.valid == False)
