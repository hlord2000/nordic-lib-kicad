#!/bin/sh
# adapted verson taken from https://github.com/Bouni/kicad-jlcpcb-tools/blob/main/PCM/create_pcm_archive.sh
# heavily inspired by https://github.com/4ms/4ms-kicad-lib/blob/master/PCM/make_archive.sh
VERSION=$1

echo "Clean up old files"
rm -f PCM/*.zip
rm -rf PCM/archive

echo "Create folder structure for ZIP"
mkdir -p PCM/archive/resources

echo "Process symbol files to update footprint references"
find symbols -type f -name "*.kicad_sym" | while read file; do
    # Create a temporary file
    temp_file="${file}.tmp"
    
    # Process the file and write to temporary file
    sed 's/"nordic-lib-kicad-/"PCM_nordic-lib-kicad-/g' "$file" > "$temp_file"
    
    # Replace original with temporary file
    mv "$temp_file" "$file"
done

echo "Copy files to destination"
cp VERSION PCM/archive
cp -r footprints PCM/archive
cp -r symbols PCM/archive
cp -r 3dmodels PCM/archive
cp -r blocks PCM/archive
cp PCM/icon.png PCM/archive/resources
cp PCM/metadata.template.json PCM/archive/metadata.json

echo "Write version info to file"
echo $VERSION > PCM/archive/VERSION

echo "Modify archive metadata.json"
sed -i "s/VERSION_HERE/$VERSION/g" PCM/archive/metadata.json
sed -i "s/\"kicad_version\": \"8.0\",/\"kicad_version\": \"8.0\"/g" PCM/archive/metadata.json
sed -i "/SHA256_HERE/d" PCM/archive/metadata.json
sed -i "/DOWNLOAD_SIZE_HERE/d" PCM/archive/metadata.json
sed -i "/DOWNLOAD_URL_HERE/d" PCM/archive/metadata.json
sed -i "/INSTALL_SIZE_HERE/d" PCM/archive/metadata.json

echo "Zip PCM archive"
cd PCM/archive
zip -r ../KiCAD-PCM-$VERSION.zip .
cd ../..

echo "Gather data for repo rebuild"
echo VERSION=$VERSION >> $GITHUB_ENV
echo DOWNLOAD_SHA256=$(shasum --algorithm 256 PCM/KiCAD-PCM-$VERSION.zip | xargs | cut -d' ' -f1) >> $GITHUB_ENV
echo DOWNLOAD_SIZE=$(ls -l PCM/KiCAD-PCM-$VERSION.zip | xargs | cut -d' ' -f5) >> $GITHUB_ENV
echo DOWNLOAD_URL="https:\/\/github.com\/hlord2000\/nordic-lib-kicad\/releases\/download\/$VERSION\/KiCAD-PCM-$VERSION.zip" >> $GITHUB_ENV
echo INSTALL_SIZE=$(unzip -l PCM/KiCAD-PCM-$VERSION.zip | tail -1 | xargs | cut -d' ' -f1) >> $GITHUB_ENV
