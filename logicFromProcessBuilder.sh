#!/bin/bash

#to launch via wsl on Windows
#<user>@<machine>:/mnt/c/<path on C drive>/circlek-sandbox$ ./logicFromProcessBuilder.sh

input_dir=force-app/main/default/flows
output_dir=logs/logic

for file in "$input_dir"/*Case_Process_Builder*; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        output_file="$output_dir/${filename}".txt
        log_file="$output_dir/${filename}.log"
        
        python3 logicFromProcessBuilder.py "$filename" > "$output_file" 2> "$log_file"
    fi
done
