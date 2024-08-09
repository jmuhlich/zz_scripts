# Reorganize Incucyte images into subfolders by well_site, e.g.
# WT_B2_1_2022y11m24d_12h30m.tif -> B2_1/

for r in A B C D E F G H; do
    for c in `seq 1 12`; do
        for p in `seq 1 4`; do
            x="${r}${c}_${p}"
            mkdir "$x"
            mv -v "WT_${x}_*tif" "$x"
            # Clean up if empty
            rmdir "$x" 2>/dev/null
            echo
        done
    done
done
