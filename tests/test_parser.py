from specmetric.parser import ComputationTreeParser
from specmetric.computation_tree import ComputationNode
from sklearn import datasets, linear_model
import numpy as np

def test_parser_leaf():
    leaf_node = ComputationNode('leaf_test', None, 'test')
    grammatical_expressions = {
        'test': {
            'input_data_type': 'test',
            'output_data_type': 'test',
            'mark_priority': [
            ]
        }
    }
    parser = ComputationTreeParser(leaf_node, grammatical_expressions=grammatical_expressions)
    parser.visualizeDFG()
    vis_containers = parser.visualization_containers

    assert len(vis_containers) == 1
    assert vis_containers[0].computation_nodes[0] == leaf_node

def test_parser_scalar_sum():
    a = 5
    b = 3
    sum_node = ComputationNode('sum', None, 'scalar_sum', input_data=['a', 'b'], output_data='aplusb')
    a_node = ComputationNode('literal_a', sum_node, 'scalar', output_data='a')
    b_node = ComputationNode('literal_b', sum_node, 'scalar', output_data='b')
    parser = ComputationTreeParser(sum_node)

    parser.visualizeDFG()
    vis_containers = parser.visualization_containers
    print(vis_containers)
    # This should result in one visualization - a single stacked bar
    assert len(vis_containers) == 1

    container = vis_containers[0]

    assert container.valid_chart == 'single_stacked_bar'
    assert 'a' in container.encodings
    assert 'b' in container.encodings

def test_parser_scatter():
    a = [3, 5, 2]
    b = [1, 1, 2]
    diff_node = ComputationNode('diff', None, 'vector_diff', input_data=['a', 'b'], output_data='aminusb')
    a_node = ComputationNode('literal_a', diff_node, 'vector', output_data='a')
    b_node = ComputationNode('literal_b', diff_node, 'vector', output_data='b')
    parser = ComputationTreeParser(diff_node)

    parser.visualizeDFG()
    vis_containers = parser.visualization_containers
    print(vis_containers)
    # This should result in one visualization - a single scatter_y_equals_x
    assert len(vis_containers) == 1

    container = vis_containers[0]

    assert container.valid_chart == 'scatter_y_equals_x'
    assert 'a' in container.encodings
    assert 'b' in container.encodings

def test_parser_r2():
    # Load the diabetes dataset
    diabetes_X, diabetes_y = datasets.load_diabetes(return_X_y=True)

    # # Use one features
    # diabetes_X = diabetes_X[:, np.newaxis, 2]

    # Split the data into training/testing sets
    diabetes_X_train = diabetes_X[:-20]
    diabetes_X_test = diabetes_X[-20:]

    # Split the targets into training/testing sets
    diabetes_y_train = diabetes_y[:-20]
    diabetes_y_test = diabetes_y[-20:]

    # Create linear regression object
    regr = linear_model.LinearRegression()

    # Train the model using the training sets
    regr.fit(diabetes_X_train, diabetes_y_train)

    # Make predictions using the testing set
    diabetes_y_pred = regr.predict(diabetes_X_test)
    y_i = diabetes_y_test
    y_hat_i = diabetes_y_pred
    X = diabetes_X_test
    y_bar_scalar = np.mean(y_i)
    y_bar_vector = np.full(y_i.shape, y_bar_scalar)
    y_i_minus_y_hat_i = y_i - y_hat_i
    y_i_minus_y_bar = y_i - y_bar_vector
    y_i_minus_y_hat_i_squared = np.square(y_i_minus_y_hat_i)
    y_i_minus_y_bar_squared = np.square(y_i_minus_y_bar)
    ss_res = np.sum(y_i_minus_y_hat_i_squared)
    ss_tot = np.sum(y_i_minus_y_bar_squared)
    one = 1
    ss_res_ss_tot_ratio = ss_res / ss_tot
    r2 = one - ss_res_ss_tot_ratio

    minus_scalar = ComputationNode('minus_scalar', None, 'scalar_diff', input_data=['one', 'ss_res_ss_tot_ratio'], output_data='r2')
    one = ComputationNode('one', minus_scalar, 'scalar', input_data=[], output_data='one')
    ratio = ComputationNode('ratio', minus_scalar, 'scalar_ratio', input_data=['ss_res', 'ss_tot'], output_data='ss_res_ss_tot_ratio')
    vector_sum_ss_tot = ComputationNode('ss_tot', ratio, 'vector_sum', input_data=['y_i_minus_y_bar_squared'], output_data='ss_tot')
    vector_sum_ss_res = ComputationNode('ss_res', ratio, 'vector_sum',input_data=['y_i_minus_y_hat_i_squared'], output_data='ss_res')
    square_variances = ComputationNode('square_variances', vector_sum_ss_tot, 'vector_square', input_data=['y_i_minus_y_bar'], output_data='y_i_minus_y_bar_squared')
    square_residuals = ComputationNode('square_residuals', vector_sum_ss_res, 'vector_square', input_data=['y_i_minus_y_hat_i'], output_data='y_i_minus_y_hat_i_squared')
    vector_difference_variances = ComputationNode('vector_difference_variances', square_variances, 'vector_diff', input_data=['y_i', 'y_bar_vector'], output_data='y_i_minus_y_bar')
    vector_difference_residuals = ComputationNode('vector_difference_residuals', square_residuals, 'vector_diff', input_data=['y_i', 'y_hat_i'], output_data='y_i_minus_y_hat_i')
    y_i_var_node = ComputationNode('literal_yi_var', vector_difference_variances, 'vector', output_data='y_i')
    broadcast = ComputationNode('broadcast_mean', vector_difference_variances, 'broadcast', input_data=['y_bar_scalar', 'y_i'], output_data='y_bar_vector')
    mean_y = ComputationNode('mean_y', broadcast, 'mean', input_data=['y_i'], output_data='y_bar_scalar')
    y_i_mean_node = ComputationNode('literal_yi_mean', mean_y, 'vector', output_data='y_i')
    y_i_res_node = ComputationNode('literal_yi_res', vector_difference_residuals, 'vector', output_data='y_i')
    y_hat_node = ComputationNode('literal_yhat', vector_difference_residuals, 'vector', output_data='y_hat_i')

    parser = ComputationTreeParser(minus_scalar)
    parser.visualizeDFG()
    vis_containers = parser.visualization_containers

    # This should result in 4 visualizations, but 3 sequences.
    # @todo, for now we aren't going to have this second level of abstraction, because
    # there are still some things to work out.  So all visualizations are part of the same
    # abstraction.
    assert len(vis_containers) == 4

    # They should be ordered by depth on the tree!
    # A pair of scatterplots with squares for marks
    res_container = vis_containers[1]
    tot_container = vis_containers[0]

    assert res_container.valid_chart == 'scatter_y_equals_x'
    assert tot_container.valid_chart == 'scatter_y_equals_x'
    assert 'y_i' in res_container.encodings
    assert 'y_hat_i' in res_container.encodings
    assert 'y_i_minus_y_hat_i' in res_container.encodings
    assert 'y_i_minus_y_hat_i_squared' in res_container.encodings
    assert 'y_i' in tot_container.encodings
    assert 'y_bar_vector' in tot_container.encodings
    # assert 'y_bar_scalar' in tot_container.encodings # not sure how this will end up there
    assert 'y_i_minus_y_bar' in tot_container.encodings
    assert 'y_i_minus_y_bar_squared' in tot_container.encodings

    # Then, a bar comparing numerator and denominator, with spacefilling marks
    container = vis_containers[2]

    assert container.valid_chart == 'bar_chart_comp'
    assert 'ss_res' in container.encodings
    assert 'ss_tot' in container.encodings
    assert 'y_i_minus_y_bar_squared' in container.encodings
    assert 'y_i_minus_y_hat_i_squared' in container.encodings

    # Then, a bar comparing 1 and the ratio
    container = vis_containers[3]

    assert container.valid_chart == 'bar_chart_diff'
    assert 'one' in container.encodings
    assert 'ss_res_ss_tot_ratio' in container.encodings

