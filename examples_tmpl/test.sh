rm -rf examples ; cp -r examples_tmpl examples
touch PREPROCESS_SAFETY_FILE.run-once
gem-taxonomy-csv-validate -c examples/csv-config.conf -s examples/helpers/sanitize_taxonomy33.sh -p examples/helpers/preprocess_taxonomy33.sh 
gem-taxonomy-csv-validate -c examples/csv-config.conf -s examples/helpers/sanitize_taxonomy33.sh
echo "First.csv:"
cat examples/files/first.csv 
echo "---------"

echo
echo "Must be as:"
cat << EOF
vvvvvvvvv
good_name,second,third
1,MR,3
a,SRC,c
^^^^^^^^^
EOF

echo
diff -q examples/files/first.csv <(cat "$0" | sed -n '/^vvvvvv/,/^\^\^\^\^/{/^vvvvvv/!{/^\^\^\^\^/!p;};}')
if [ $? -eq 0 ]; then
    echo "They match"
else
    echo "They diff"
    diff examples/files/first.csv <(cat "$0" | sed -n '/^vvvvvv/,/^\^\^\^\^/{/^vvvvvv/!{/^\^\^\^\^/!p;};}')
fi

