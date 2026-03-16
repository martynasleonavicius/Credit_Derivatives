#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script contains code to find bond spread of a specific company

"""

import numpy as np
from datetime import date
import scipy.optimize


# Structure of bonds dictionary: "COMPANY_NAME":[COUPON_RATE, MATURITY, LAST_PRICE, YIELD, LAST_TRADE_DATE]
# Assume bonds have yearly coupons.
# We will use actual/365 date-count convention.
# YIELD and LAST_TRADE_DATE are not actively used. They were written here for completness 
bonds = {
    "Petroleos Mexicanos": [6.84, '1/23/2030', 101.03, 6.53, '3/12/2026'],
    "Mars INC DEL": [4.8, '2/1/2030', 101.41, 4.4, '3/12/2026']
    }


# A function to convert maturity dates into datetime objects 
def convert_string_to_date(maturity):
    format = '%m/%d/%Y'
    datetime_object = date.strptime(maturity, format)
    return datetime_object


# Calculates how many days are left from today to bond's maturity.
def time_to_maturity(company_name) -> int:
    time_now = date.today()
    maturity = convert_string_to_date(bonds[company_name][1])
    return (maturity - time_now).days

def years_to_maturity(company_name):
    years_left = time_to_maturity(company_name)/365
    fraction = years_left%1
    return int(years_left-fraction), fraction # Let us take care in returning years_left as a whole number

# Calculates the number of coupon payments based on time to maturity, with an assumption that they are paid once a year.
def number_of_payments(company_name) -> int:
    years_left, fraction = years_to_maturity(company_name)
    if fraction == 0:
        return years_left   # Only if coupon was paid today. Also, we ignore the existence of leap years (as per actual/365 convention)
    return years_left + 1   # Return one more than years left because a coupon payment is due in less than a year
    

# For more accuracy, we could interpolate the risk-free rates on the days when we expect the coupon payment based on the actual zero-yield curve
def accurate_risk_free(rates_fred, company_name):
    years_left, fraction = years_to_maturity(company_name)
    next_payment = fraction if fraction > 0 else 1  # We define when the next payment should be
    accurate_rates = {}     # Dictionary for interpolated continuously compounded zero rates.
    # NOTE: if there is less than half a year left until the first coupon payment, we will use 0.5 discount rate for simplicity.
    # Similarly, for any payments in more than 30 years, we will use 30 year rates
    for year in range(number_of_payments(company_name)):
        if next_payment <= 0.5:
            accurate_rates[next_payment] = np.log(1 + rates_fred[0.5]/100)
        elif next_payment >= 30:
            accurate_rates[next_payment] = np.log(1 + rates_fred[30]/100)
        else:
            accurate_rates[next_payment] = interpolation(rates_fred, next_payment)
        next_payment += 1
    return accurate_rates
    


# Function that linearly interpolates continuously compounding zero rates for coupon payments 
def interpolation(rates_fred, next_payment):
    years = np.array(list(rates_fred.keys()))
    # We need to find years for which we know discount rates from FRED.
    last_year = float(years[years <= next_payment][-1])    # Define this to be <= next_payment date
    next_year = float(years[years >= next_payment][0])    # Define this to be >= next_payment date
    b = (rates_fred[next_year] - rates_fred[last_year])/(next_year - last_year)     # Find the slope
    a = rates_fred[last_year] - b*last_year    # Find the intercept
    
    return np.log(1 + (a + b*next_payment)/100)   # Return risk-free rate as a continuous compounding rate


# Before we continue, we need to define present value calculation function for bond's present value
def dirty_bond_PV(spr, coupon, face, accurate_rates, company_name):
    pv = sum(coupon * np.exp(-t * (r + spr)) for t, r in accurate_rates.items())  #present value of all discounted coupon payments
    t_fin, frac = years_to_maturity(company_name)       # See how many years are left to maturity. t_fin is a whole integer, while frac is the fraction of the remaining year until the default
    r_fin = accurate_rates[t_fin + frac]    # Find the final discount rate
    pv += face * np.exp(-(t_fin + frac) * (r_fin + spr)) # Discount face value
    pv += coupon*(1-frac)   # add accrued interest, because the quoted market price is dirty! frac IS the remainder of the year until next coupon payment.
    return pv

# Define the objective of minimizing the difference between the calculated dirty bond price and actual market value
def objective(spr, coupon, face, accurate_rates, market_val, company_name):
    return dirty_bond_PV(spr, coupon, face, accurate_rates, company_name) - market_val

# Now it is time to find the spread of the bond
def spread(rates_fred, company_name):
    coupon = bonds[company_name][0]    # Coupon rate
    market_val = bonds[company_name][2]    # Market value
    accurate_rates = accurate_risk_free(rates_fred, company_name)   # Risk free rates
    face = 100
    spr = scipy.optimize.brentq(objective, -0.01, 0.1, args=(coupon, face, accurate_rates, market_val, company_name))    # bond spread
    return spr































