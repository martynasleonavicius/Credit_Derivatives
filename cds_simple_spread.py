# -*- coding: utf-8 -*-

"""
This script is a simple demonstration of how credit default swaps spreads are calculated.
The calculation method used here comes from the book "Options, Futures, and Other Derivatives" by John C Hull, 7th edition
See chapter 23.2 pg 520.
"""

import pandas as pd
import numpy as np

recovery_rate = 0.4
r = 0.05                #Assumed continuously compounding rate
T = 100                   #Maturity of the contract. Set large to demonstrate spread stability across maturities
p = 0.02                #Probability that the company will default


#For simplicity, we assume that payments are made every year with the first one being 1 year from now

years = {
        "Year":[i for i in range(1,T+1)]
        }

payment_values = pd.DataFrame(years) #Here we save all the relevant information used for valuing the present made to the protection seller
payment_values['Survival probability'] = (1-p)**payment_values['Year']
payment_values['Discount factor'] = np.exp(-r * payment_values['Year'])
payment_values['PV of probability weighted payment for protection'] = payment_values['Discount factor'] * payment_values['Survival probability']


#Assume the default happens mid-year
years = {"Year":[i+0.5 for i in range(T)]}
default_value = pd.DataFrame(years)  #Here we save information for valuing the payout incase of a default
default_value['Default probability'] = p*(1-p)**(payment_values['Year'] - 1) #We use such a formula because the company needs to survive (1-p)^(m-1) before defaulting on mth year
default_value['Discount factor'] = np.exp(-r * default_value['Year'])
default_value['PV of probability weighted payment in case of a default'] = default_value['Discount factor'] * default_value['Default probability'] * (1-recovery_rate) #We add the last factor because a protection seller would need to payout the amount that cannot be rocovered


#Also, we need to calculate the accrual of protection.
#Because the default happens mid year, the protection buyer still needs to pay for the time company does not default
accrual_value = pd.DataFrame()
accrual_value['PV of probability weighted accrual payment in case of a default'] = default_value['Discount factor'] * default_value['Default probability']/2 #We divide by 2 because the accrual payment is for half a year

CDS_spread = (default_value['PV of probability weighted payment in case of a default']).sum()/sum(payment_values['PV of probability weighted payment for protection'] + accrual_value['PV of probability weighted accrual payment in case of a default'])

print(f"Credit default swap spread is {'%.3f.'%(CDS_spread*10000)} basis points")


#NOTE: when using flat discount curves, the cds spread is the same for T=1, 5, and 100 up to 3 decimal places.
#=> spread has no meaningful dependence on maturity. This is because the expected default payment value decays rapidly with each succesive year.


