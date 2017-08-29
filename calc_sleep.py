import csv
import sys
import math
from datetime import datetime, timedelta

BIN_LENGTH_IN_SECONDS = 60 * 60

sleeps = []
first_day = None
last_day = None
with open(sys.argv[1]) as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        start = datetime.strptime(row[1], '%m/%d/%y, %I:%M %p')
        end = start + timedelta(minutes=int(row[2]))
        sleeps.append((start, end, (end - start).total_seconds()))

        if first_day is None or start < first_day:
            first_day = start
        if last_day is None or end > last_day:
            last_day = end

# first bin is the start of the first day in the range, not the first recorded hour
bins = [ { "seconds": 0, "count": 0 } for x in range(math.ceil((last_day - first_day).total_seconds() / BIN_LENGTH_IN_SECONDS))]
first_bin = datetime(first_day.year, first_day.month, first_day.day)

for (i, bin) in enumerate(bins):
    bin_start = first_bin + timedelta(seconds=BIN_LENGTH_IN_SECONDS * i)
    bin_end = bin_start + timedelta(seconds=BIN_LENGTH_IN_SECONDS)
    for sleep in sleeps:
        starts_before_bin = sleep[0] < bin_start
        starts_during_bin = sleep[0] >= bin_start and sleep[0] < bin_end
        ends_after_bin = sleep[1] > bin_end
        ends_during_bin = sleep[1] >= bin_start and sleep[1] < bin_end

        addition = 0
        if starts_during_bin and ends_during_bin:
            addition = sleep[2]
        elif starts_before_bin and ends_after_bin:
            addition = BIN_LENGTH_IN_SECONDS
        elif starts_before_bin and ends_during_bin:
            addition = (sleep[1] - bin_start).total_seconds()
        elif starts_during_bin and ends_after_bin:
            addition = (bin_end - sleep[0]).total_seconds()

        if addition > 0:
            bins[i]['seconds'] += addition
            bins[i]['count'] += 1

summary_bins_week = [ { 'seconds': 0, 'count': 0 } for x in range(int(7 * 24 * 60 * 60 / BIN_LENGTH_IN_SECONDS))]
summary_bins_day = [ { 'seconds': 0, 'count': 0 } for x in range(int(24 * 60 * 60 / BIN_LENGTH_IN_SECONDS))]

for (i, bin) in enumerate(bins):
    bin_start = first_bin + timedelta(seconds=BIN_LENGTH_IN_SECONDS * i)
    bin_end = bin_start + timedelta(seconds=BIN_LENGTH_IN_SECONDS)
    day_of_week = (bin_start.weekday() + 1) % 7
    hour_of_day = bin_start.hour

    summary_bin_weekly_i = int(day_of_week * 24 * 60 * 60 / BIN_LENGTH_IN_SECONDS) + int(hour_of_day * 60 * 60 / BIN_LENGTH_IN_SECONDS)
    summary_bin_daily_i = int(hour_of_day * 60 * 60 / BIN_LENGTH_IN_SECONDS)

    summary_bins_week[summary_bin_weekly_i]['seconds'] += bin['seconds']
    summary_bins_week[summary_bin_weekly_i]['count'] += 1

    summary_bins_day[summary_bin_daily_i]['seconds'] += bin['seconds']
    summary_bins_day[summary_bin_daily_i]['count'] += 1

with open('day.tsv', 'w') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(('hour', 'sleep (min)', 'count', 'avg (min)'))
    for (i, bin) in enumerate(summary_bins_day):
        row = [i]
        row.append(bin['seconds'] / 60.0)
        row.append(bin['count'])
        row.append(bin['seconds'] / (bin['count'] * 60.0))
        writer.writerow(row)

with open('week.tsv', 'w') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(('dow', 'hour', 'sleep (min)', 'count', 'avg (min)'))
    for (i, bin) in enumerate(summary_bins_week):
        row = []
        row.append(math.floor(i * 60 * 60 / (BIN_LENGTH_IN_SECONDS * 24))) # day of week
        row.append((i * 60 * 60 / BIN_LENGTH_IN_SECONDS) % 24) # hour of day
        row.append(bin['seconds'] / 60.0)
        row.append(bin['count'])
        row.append(bin['seconds'] / (bin['count'] * 60.0))
        writer.writerow(row)

