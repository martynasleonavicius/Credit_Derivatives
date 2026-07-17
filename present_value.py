#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The purpose of this file is to numerically interpolate zero coupon bond rates.

Specifically, as we assume linear rate dependency in between rates provided by FRED, we thus have r(t) = a + bt, where a and b are of out interest.

One of the uses for intercept and the slope will be to calculate appropriate rates to discount bond's coupon payments.
The other purpose is to use a and b explicitly in caclulating accrude protection and protection payment upon a default as we shall allow a company to default at any time between coupon payments. 
"""

import numpy as np
from scipy.special import erf
from scipy.special import erfi



# Let us find the intercept and the slope of the zero rate curve.
# NOTE: these quantities need to be recalculated if 
def find_intercept_and_slope(rates_fred, next_payment):
    years = np.array(list(rates_fred.keys()))
    # We need to find years for which we know discount rates from FRED.
    last_year = float(years[years <= next_payment][-1])    # Set this to represent last zero rate reported by FRED before coupon payment 
    next_year = float(years[years >= next_payment][0])    # Same thing as above but for reported zero rates after the coupon payment
    b = (rates_fred[next_year] - rates_fred[last_year])/(next_year - last_year)     # Find the slope
    a = rates_fred[last_year] - b*last_year    # Find the intercept
    
    return a, b

# Calculates appropriate discount for coupon payments (ie intepolates from current zero rate curves)
def coupon_payment_discount(rates_fred, next_payment):
    a, b = find_intercept_and_slope(rates_fred, next_payment)
    return a + b*next_payment

#There is a reocuring need to call the error function
def help_erf(a, b, hazard_rate, t):
    if b > 0:
        return erf((a + 2*b*t + hazard_rate)/(2*np.sqrt(b)))
    return erfi((a - 2*b*t + hazard_rate)/(2*np.sqrt(-b)))    #Use imaginary error function to handle negative b values
                                                            

# Calculates the present value of a default payment WITHOUT ANY RESTRICTIONS AS TO WHEN THE COMPANY CAN DEFAULT
def pv_default_payment(recovery_rate, hazard_rate, rates_fred, next_payment, Notional = 1):
    a, b = find_intercept_and_slope(rates_fred, next_payment)
    
    previous_payment = next_payment - 1 if next_payment > 1 else 0
    
    if b != 0:
        temp1 = help_erf(a, b, hazard_rate, next_payment)
        temp2 = help_erf(a, b, hazard_rate, previous_payment)
    
    
    if b > 0:   #Zero curve is increasing
        return hazard_rate*Notional*(1 - recovery_rate)*np.exp(((a + hazard_rate)**2)/(4*b))*np.sqrt(np.pi)*(temp1 - temp2)/(2*np.sqrt(b))
    
    elif b == 0:    #Flat zero curve
        return hazard_rate*Notional*(1 - recovery_rate)*(np.exp(-previous_payment * (a + hazard_rate)) - np.exp(-next_payment * (a + hazard_rate)))
    
    #Inverted zero curve
    return hazard_rate*Notional*(1 - recovery_rate)*np.exp(((a + hazard_rate)**2)/(-4*b))*np.sqrt(np.pi)*(temp1 - temp2)/(2*np.sqrt(-b))


#Calculate the present value of the accrude payments when allowing the company to default at any time
def pv_accrude_payment(recovery_rate, hazard_rate, rates_fred, next_payment, Notional = 1):
    a, b = find_intercept_and_slope(rates_fred, next_payment)
    
    previous_payment = next_payment - 1 if next_payment > 1 else 0
    
    if b != 0:
        temp1 = help_erf(a, b, hazard_rate, next_payment)
        temp2 = help_erf(a, b, hazard_rate, previous_payment)
        temp3 = (a + hazard_rate)/(2 * b)
    
    pv = pv_default_payment(recovery_rate, hazard_rate, rates_fred, next_payment)
    
    
    print(b)
    
    if b > 0:   #Increasing zero curve
        return (hazard_rate**2)*Notional*(1 - recovery_rate)*np.exp(((a + hazard_rate)**2)/(4*b)) * (
            np.sqrt(np.pi * b) * ((a + hazard_rate)/( 2 * b)) * (temp2 - temp1) + np.exp(-b * ((previous_payment + temp3)**2)) - np.exp(-b * ((next_payment + temp3)**2))
            )/(2*b * (next_payment - previous_payment)) - pv * previous_payment * hazard_rate / ((1 - recovery_rate) * (next_payment - previous_payment))
    
    elif b == 0: #flat zero curve
        return ((hazard_rate**2)*Notional*(1 - recovery_rate) * (np.exp(-previous_payment * (a + hazard_rate)) - np.exp(-next_payment * (a + hazard_rate))) *
                (1/(a + hazard_rate) + 1/((a + hazard_rate)**2)) - previous_payment * hazard_rate * pv / (next_payment - previous_payment))
    
    #Inverted zero curve
    return (hazard_rate**2)*Notional*(1 - recovery_rate)*np.exp(((a + hazard_rate)**2)/(4*b)) * (
        np.sqrt(np.pi * b) * ((a + hazard_rate)/( 2 * b)) * (temp2 - temp1) - np.exp(b * ((previous_payment + temp3)**2)) + np.exp(b * ((next_payment + temp3)**2))
        )/(2*b * (next_payment - previous_payment)) - pv * previous_payment * hazard_rate / ((1 - recovery_rate) * (next_payment - previous_payment))
    

#NOTE: The expressions above have been deived by me and then checked using wolframalpha if the integrals were correct.
#I used my own intuition and knowledge as to how set-up corerect integrals for calculating these quantities and I explain in detail how
#I arrived here in README


