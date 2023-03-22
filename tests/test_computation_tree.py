from specmetric.computation_tree import ComputationNode

def test_uuid_initialization():
	cn1 = ComputationNode(None, None, None)
	cn2 = ComputationNode(None, None, None)
	assert cn1.uuid != cn2.uuid