import yaml
try:
    from importlib import resources as res
except ImportError:
    import importlib_resources as res

# with res.open_binary('spam', 'config.yml') as fp:
#     config = yaml.load(fp, Loader=yaml.Loader)

grammatical_expressions = {}
with res.open_binary('specmetric.rules', 'grammatical_expressions.yml') as fp:
    grammatical_expressions = yaml.load(fp, Loader=yaml.Loader)
# with open("./rules/grammatical_expressions.yml") as stream:
	# try:
	# 	grammatical_expressions = yaml.safe_load(stream)
	# except yaml.YAMLError as exc:
	# 	print(exc)

compositions = {}
with res.open_binary('specmetric.rules', 'compositions.yml') as fp:
    compositions = yaml.load(fp, Loader=yaml.Loader)
# with open("./rules/compositions.yml") as stream:
	# try:
	# 	compositions = yaml.safe_load(stream)
	# except yaml.YAMLError as exc:
	# 	print(exc)

