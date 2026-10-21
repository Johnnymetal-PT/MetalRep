#!/bin/bash

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Create download directory if it doesn't exist
mkdir -p ../download

# Create a timestamp for the output file
timestamp=$(date +"%Y%m%d_%H%M%S")
# Use tomorrow's date for the output file name
output_file="../download/$(date -d "+1 day" +"%d_%m_%Y")_feed.csv"
echo "Output will be saved to: $output_file"

# Run the spider starting from page 1
page=1
first_run=true
consecutive_empty=0  # Counter for consecutive empty results

while true; do
    echo "Starting spider for page $page..."
    
    # For the first run, create a new file. For subsequent runs, append without header
    if [ "$first_run" = true ]; then
        output=$(scrapy crawl spider-hipermercados-updated-zenrows -a start_page=$page -o "$output_file" --loglevel=DEBUG 2>&1)
        first_run=false
    else
        # Create a temporary file for the new data
        temp_file="temp_${timestamp}.csv"
        output=$(scrapy crawl spider-hipermercados-updated-zenrows -a start_page=$page -o "$temp_file" --loglevel=DEBUG 2>&1)
        
        # If the temp file was created and has content, append its data (excluding header) to the main file
        if [ -f "$temp_file" ] && [ $(wc -l < "$temp_file") -gt 1 ]; then
            # Skip the header line and append the rest
            tail -n +2 "$temp_file" >> "$output_file"
            rm "$temp_file"
            consecutive_empty=0  # Reset counter if we found items
        else
            ((consecutive_empty++))  # Increment counter if no items found
            if [ -f "$temp_file" ]; then
                rm "$temp_file"
            fi
        fi
    fi
    
    exit_code=$?
    
    # Display the output
    echo "Spider output:"
    echo "$output"
    
    # Check if the CSV file exists and has content
    if [ -f "$output_file" ]; then
        line_count=$(wc -l < "$output_file")
        echo "CSV file has $line_count lines"
        if [ $line_count -gt 1 ]; then
            echo "First few lines of CSV:"
            head -n 3 "$output_file"
        else
            echo "WARNING: CSV file exists but appears empty!"
            echo "Last spider output:"
            echo "$output" | tail -n 50
        fi
    else
        echo "WARNING: CSV file was not created!"
        echo "Last spider output:"
        echo "$output" | tail -n 50
    fi
    
    # Check if we should stop
    if [ $consecutive_empty -ge 3 ]; then
        echo "Stopping spider: 3 consecutive attempts with no new items found"
        break
    fi
    
    # Check if the spider encountered an error or no more products
    if [[ $exit_code -ne 0 ]] || [[ $output == *"No products found on this page"* ]] || [[ $output == *"No next page link found"* ]]; then
        echo "Stopping spider:"
        if [[ $exit_code -ne 0 ]]; then
            echo "Error occurred (exit code: $exit_code)"
            echo "Last output:"
            echo "$output" | tail -n 50
        elif [[ $output == *"No products found on this page"* ]]; then
            echo "No products found on page $page"
        elif [[ $output == *"No next page link found"* ]]; then
            echo "No more pages available"
        fi
        break
    fi
    
    echo "Finished page $page"
    # Optional: add a small delay between runs
    sleep 2
    
    # Increment page number
    ((page++))
done

echo "Spider completed! Results saved to $output_file"
echo "Final CSV file size: $(wc -l < "$output_file") lines" 