from datetime import timedelta, date, datetime, time
from itertools import islice, islice
import itertools
from google.appengine.ext import db
import fuel


class FuelCacheMonth(db.Model):
    year = db.IntegerProperty()
    month = db.IntegerProperty()

    liters = db.FloatProperty()
    km = db.FloatProperty()

    def liters_per_km(self):
        return self.liters/self.km

class FuelCacheWeek(db.Model):
    year = db.IntegerProperty()
    week = db.IntegerProperty()

    liters = db.FloatProperty(default=0.0)
    km = db.FloatProperty(default=0.0)

    def liters_per_km(self):
        return self.liters/self.km


def timedelta_fraction(small,big):
    seconds_small = float(small.days)*3600.0*24.0 + float(small.seconds) + float(small.microseconds)/1000000.0
    seconds_big = float(big.days)*3600.0*24.0 + float(big.seconds) + float(big.microseconds)/1000000.0

    return seconds_small/seconds_big

def updateWeekCache(out):
    for w in FuelCacheWeek.all(): w.delete()


    start_date =  fuel.Refueling.all().order('date').get().date.date()
    first_week_date = start_date - timedelta(start_date.isocalendar()[2]-1)
    last_week_date = date.today() - timedelta(date.today().isocalendar()[2]-1)

    weeks = {}

    cur_week_date = first_week_date


    while cur_week_date <= last_week_date:
        y,w = cur_week_date.isocalendar()[:2]
        weeks[(y,w)] = FuelCacheWeek(year=y,week=w)
        cur_week_date += timedelta(7)

    q = fuel.Refueling.all().order('date')
    cur_refuel = q.get()
    for r in itertools.islice(q,1,None):
        prev_refuel = cur_refuel
        cur_refuel = r

        total_time = cur_refuel.date - prev_refuel.date
        total_liters = prev_refuel.rest_liters + prev_refuel.liters - cur_refuel.rest_liters
        total_km = float(cur_refuel.odo - prev_refuel.odo)

        cur_time = prev_refuel.date

        while 1:

            year, weekno, weekday = cur_time.isocalendar()
            next_week_start = datetime.combine(cur_time.date() + timedelta(8-weekday),time(0,0,0))
            if next_week_start < cur_refuel.date:
                weeks[(year,weekno)].liters += timedelta_fraction(next_week_start-cur_time,total_time) * total_liters
                weeks[(year,weekno)].km += timedelta_fraction(next_week_start-cur_time,total_time) * total_km
                cur_time = next_week_start
            else:
                weeks[(year,weekno)].liters += timedelta_fraction(cur_refuel.date-cur_time,total_time) * total_liters
                weeks[(year,weekno)].km += timedelta_fraction(cur_refuel.date-cur_time,total_time) * total_km
                break

    for w in weeks.itervalues():
        w.save()

    print  >> out, "total km = %.2f" % sum(w.km for w in weeks.itervalues())
    print  >> out,"total l = %.2f" % sum(w.liters for w in weeks.itervalues())




        




    
    
    
