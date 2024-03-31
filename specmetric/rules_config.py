import yaml
try:
    from importlib import resources as res
except ImportError:
    import importlib_resources as res

grammatical_expressions = {}
with res.open_binary('specmetric.rules', 'grammatical_expressions.yml') as fp:
    grammatical_expressions = yaml.load(fp, Loader=yaml.Loader)['expressions']

spreadsheet_grammatical_expressions = {}
with res.open_binary('specmetric.rules', 'spreadsheet_grammatical_expressions.yml') as fp:
    spreadsheet_grammatical_expressions = yaml.load(fp, Loader=yaml.Loader)['expressions']

compositions = {}
with res.open_binary('specmetric.rules', 'compositions.yml') as fp:
    compositions = yaml.load(fp, Loader=yaml.Loader)['compositions']
