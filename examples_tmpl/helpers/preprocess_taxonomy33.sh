#!/bin/bash
sed -u 's/\bb\b/SRC/g' | \
sed -u 's/\b2\b/222/g' | \
cat
