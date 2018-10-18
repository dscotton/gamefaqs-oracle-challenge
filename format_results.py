#!/usr/bin/python

# Format the results into the format used by FANN.

import re

results_file = open('results2.txt', 'r')
results_text = results_file.read()
results = results_text.split('\n')

output = ''

while '' in results:
    results.remove('')

for result in results:
    match = re.split('[^0-9.]+', result)
    comp1 = match[1]
    comp2 = match[2]
    percent = float(match[3])
    percent = percent / 100
    year = int(match[4])

    if year == 3:
        # skip the games contest
        continue
    if year == 4:
        year = 3
    if year == 5 or year == 6:
        year = 4
        
    output += '%s %s %s\n%s\n' % (comp1, comp2, year, percent)

outfile = open('formatted_results.txt', 'w')
outfile.write(output)
