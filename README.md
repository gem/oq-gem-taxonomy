# Python OpenQuake Gem Taxonomy

python package with GEM Building Taxonomy related class and shell commands.

## Python Code

This package provide one class: ``GemTaxonomy``

with public methods:

``validate(tax_string)``: validate a taxonomy string and return it in a couple of useful structures

``explain(tax_string, format)``: explain (or translate) to different formats a taxonomy string

Below a small usage example:

```python
from openquake.gem_taxonomy import GemTaxonomy

gt = GemTaxonomy()


def validate_gem_taxonomy(value):
    try:
        gt.validate(value)
    except ValueError as e:
        print(f"Error: {e}")
        return f'{value}: {e}'


def extract_attributes(value):
        # Function to extract attributes
        attr_dict = gt.split_by_attributes(value, '|', 0, 'others')
        return attr_dict
```

[scripts.py](https://github.com/gem/oq-gem-taxonomy/blob/main/openquake/gem_taxonomy/scripts.py) is another good entry-point to understand how to use ``GemTaxonomy`` class.

## Console Commands

The package includes several command line tools using the python class to perform different tasks.

``gem-taxonomy-validate``: validate taxonomy string passed as parameter

``gem-taxonomy-csv-validate``: validate taxonomy strings from a csv file (or a list of them) with a lot options to replace values if needed, it is used extensively for CI pipelines

``gem-taxonomy-explain``: explain (or convert) taxonomy strings to different formats

``gem-taxonomy-info``: retrieves information about the taxonomy package and related packages

``gem-taxonomy-specs2graph``: create a ``.dot`` file that explains relations between atoms groups and attributes.

