#!/bin/bash
PKG_VERS="$1"
sed -i 's@](\./LICENSE)@](https://github.com/gem/oq-gem-taxonomy-data/blob/'"$PKG_VERS"'/LICENSE)@g;s@](\./DATA_LICENSE)@](https://github.com/gem/oq-gem-taxonomy-data/blob/'"$PKG_VERS"'/DATA_LICENSE)@g' README.md
