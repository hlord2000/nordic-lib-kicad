for file in ./symbols/*.kicad_sym; do
    ./kicad-library-utils/klc-check/check_symbol.py "$file" -vv
done

for file in ./footprints/*.pretty/*; do
    ./kicad-library-utils/klc-check/check_footprint.py "$file" -vv
done

