





import random

# OUR ACCOUNT PLAYS 3.2 DAYS A WEEK


def hours_normilized_random(hours):
  pass
  # Normilized formula for the hours, but max hours are 10, min hours are 2


account_days_play_a_week = 3.2  # FLOAT
days_of_the_week_number = 7 # FLOAT

days_of_the_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Satudrday', 'Sunday']
scheduler_of_the_week = {
  "Monday": -1,
  'Tuesday': -1,
  'Wednesday': -1,
  'Thursday': -1,
  'Friday': -1,
  'Satudrday': -1,
  'Sunday': -1
}

for day in days_of_the_week:
  result = random.uniform(0, 1)
  if account_days_play_a_week / days_of_the_week_number <= result:
    scheduler_of_the_week[day] = 0

days_per_year_offs = 12
days_per_year = 365

for day in days_of_the_week:
  result = random.uniform(0, 1)
  if days_per_year_offs / days_per_year <= result:
    scheduler_of_the_week[day] = -1



hours_per_day_played = 5 # FLOAT

for day in days_of_the_week:
  if scheduler_of_the_week[day] == -1:
    continue

  scheduler_of_the_week[day] = hours_normilized_random(hours_per_day_played)

(20, 150, 75)
