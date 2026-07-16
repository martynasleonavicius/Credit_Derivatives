#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script evaluates the CDS contract spanning from the contract inception date to bond's maturity
ASSUMPTIONS:
    -The company can only default during the middle of the year or half way between coupon payment and creation of a CDS
    -Spread represents ONLY the risk of default. Thus spread calculated using spread_calculator shall be used here to evaluate the probability of a default.
    -Recovery is set to 40%

NOTE: 'Event probability' in the default table holds unconditional default probabilities, while the insurance table holds survival ones

The technique to price a CDS contract was taken from John C Hull's book 'Options, Futures, and Other Derivatives' 7th edition, chapter 23.
The default probability calculations were based on techniques from chapter 22 .

"""
from yield_curve_getter import rates
from spread_calculator import spread, years_to_maturity, number_of_payments, accurate_risk_free
from present_value import coupon_payment_discount
import pandas as pd
import numpy as np

# Calculates the probability for the company to survive up to time t from the inception of the contract
def probability_of_survival(hazard_rate, t):
    return np.exp(-hazard_rate * t)

# Given a hazard rate, this function calculates the probability for a company to survive between times t_i and t_n
def probability_of_default(hazard_rate, t_i, t_n):
    return np.exp(-hazard_rate * t_i) - np.exp(-hazard_rate * t_n)


# Computes continuously compounded zero rates at expected default times.
def discount_curve_on_default(rates_fred, company_name):
    years_left, fraction = years_to_maturity(company_name)
    next_default = fraction/2 if fraction > 0 else 1/2  # We define when the next default could be
    accurate_rates = {}     # Dictionary for interpolated zero rates
    
    # NOTE: if there is less than 0.5 years left until the first possible default, we will use 0.5 zero rate for simplicity.
    # Similarly, for any payments in more than 30 years, we will use 30 year rates
    # This is just for the first default, which, as we have defined, can happen halfway between writing the contract and the first coupon payment
    accurate_rates[next_default] = rates_fred[0.5]

    # After this we can go back to assuming that defaults may in the middle of the year, ie between payments
    next_default = 1.5
    
    for year in range(1, number_of_payments(company_name)): # We already accounted for the first one
        if next_default >= 30:

            accurate_rates[next_default] = rates_fred[30]
        else:
            accurate_rates[next_default] = coupon_payment_discount(rates_fred, next_default)
                
        next_default += 1
    return accurate_rates
    

# Populate year and discount columns for each table
def populate_tables(df, hazard_rate, rates_fred, company_name, curve):
    continuously_compounding_zero_rates = curve(rates_fred, company_name)
    df["Year"] = list(continuously_compounding_zero_rates.keys())
    df["Discount"] = list(continuously_compounding_zero_rates.values())

# Calculate the unconditional default probabilities of each period
def add_default_probabilities(hazard_rate):
    prob_of_default = []
    t_i = 0     # Set time of contract inception
    for t_n in default_table["Year"]:
        prob_of_default.append(probability_of_default(hazard_rate, t_i, t_n))   # Save probability of default between t_i and t_n
        t_i = t_n
    default_table['Event probability'] = prob_of_default
    
    
# Here we calculate the expected payouts at all times we have allowed 
def expected_insurance_expense(df, Notional = 1):   # For insurance against the default
    df['Expected payout'] = Notional*df['Event probability']*df["Discount"] 
def expected_default_expense(df, Notional = 1):     # For expected payout incase of a default
    df['Expected payout'] = Notional*df['Event probability']*df["Discount"]*(1 - recovery_rate)

# Now let us calculate the survival probabilities up to some time t and populate the insurance_table with them
def add_survival_probabilities(hazard_rate):
    prob_of_survival = []
    for t in insurance_table["Year"]:
        prob_of_survival.append(probability_of_survival(hazard_rate, t))
    insurance_table['Event probability'] = prob_of_survival      
        
        

# Lastly, we need to calculate any accrued payments. These are payments that are made for the insurance in the period from the last scheduled payment to the default.
# Because we allow defaults to happen in right inbetween payments, we can see that:
#    -accrued payment will be =(insurance payment)*(fraction of the year from last payment)
#    -Probability of those payments actually happening is equal to the default probability
def accrued_payment_table(accrued_table, Notional = 1):
    accrued_table['Year'] = default_table['Year']   # Copy years when accrued payments can happen
    accrued_table['Discount'] = default_table['Discount']   # Use relevant discounts
    accrued_table['Event probability'] = default_table['Event probability'] #Use relevant probabilities
    # For the following, the insurance_table and default_table are aligned 
    accrued_table['Fraction of the year to default'] = insurance_table['Year'] - default_table['Year']  # Find relevant fraction of the year for which the protection needs to be paid
    accrued_table['Expected payout'] = Notional * accrued_table['Fraction of the year to default'] * accrued_table['Event probability'] * accrued_table['Discount']    # Calculate the expected accrued protection payment in a single period
        

# We finally have all the pieces to calculate the CDS spread
def cds_spread(insurance_table, accrued_table, default_table):
    return 10000 * sum(default_table['Expected payout'])/(accrued_table['Expected payout'] + insurance_table['Expected payout']).sum()

     
        
        
        
if __name__ == "__main__":
    
    company_name = "Petroleos Mexicanos"   #Currently there are 2 different companies' bonds hardcoded for which CDS pricing is available here.
                                    #They are Mars INC DEL and Petroleos Mexicanos. Market information last updated on 12/03/2026
    
    rates_fred = rates()
    
    recovery_rate = 0.4

    hazard_rate = spread(rates_fred, company_name)/(1 - recovery_rate)
    
    
    default_table = pd.DataFrame()      # saves information relevant to calculating expected payments upon a default
    insurance_table = pd.DataFrame()    # save information to calculate expected value of payments for a protection buyer
    accrued_table = pd.DataFrame()   # accrued payment schedule
    populate_tables(default_table, hazard_rate, rates_fred, company_name, discount_curve_on_default)
    populate_tables(insurance_table, hazard_rate, rates_fred, company_name, accurate_risk_free)
    add_survival_probabilities(hazard_rate)
    add_default_probabilities(hazard_rate)
    expected_insurance_expense(insurance_table)
    expected_default_expense(default_table)
    accrued_payment_table(accrued_table)
    
    print(f"Spread is: {cds_spread(insurance_table, accrued_table, default_table)} basis points (bps)")

























