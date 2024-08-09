keys=`aws s3api list-objects-v2 --bucket htan-dcc-hms --prefix imaging_level_2/ --query "Contents[? contains(Key, '73-8') || contains(Key, '73-9')].Key" --output text`

for src in $keys; do
    dest=`echo $src | sed -e 's/imaging_level_2\///'`
    echo aws s3 cp s3://htan-dcc-hms/$src s3://lin-2021-crc-atlas/data/$dest --storage-class INTELLIGENT_TIERING
done > copy1-commands.sh
