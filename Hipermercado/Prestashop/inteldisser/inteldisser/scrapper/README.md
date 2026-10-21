## hipermercado-pt-eldisser

# Install the requirements
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
pip3 install scrapy_playwright
pip3 install scrapy_zenrows
playwright install

# Export the CSV - Can be executed in the cron script
scrapy crawl spider-hipermercados-updated-zenrows -o output.csv
chmod +x run_spider.sh