import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd

def calc_national_insurance(salary):        
    # Class 1 NIC
    contribution = 0
    pt, uel = 9.546, 50.270
    if salary > uel:
        contribution = (salary - uel) * 0.02 + (uel - pt) * 0.12
    elif salary > pt:
        contribution = (salary - pt) * 0.12
    return contribution

def calc_income_tax_considering_personalallowance(income):
    bands_and_tax_rates = [\
    ( 0     ,  12.570, 0.0 ),\
    ( 12.570,  50.270, 0.2 ),\
    ( 50.270, 150.000, 0.4 ),\
    (150.000, 999.000, 0.45)]
    
    tax = 0;
    income_still_to_be_taxed = income
    for band_and_tax_rate in bands_and_tax_rates:
        income_in_bracket = min(income_still_to_be_taxed, band_and_tax_rate[1] - band_and_tax_rate[0])
        tax = tax + (income_in_bracket * band_and_tax_rate[2])
        income_still_to_be_taxed = income_still_to_be_taxed - income_in_bracket
        if income_still_to_be_taxed <= 0:
            break
    return tax

def calc_income_after_tax_and_NI(working, income):
    income_tax = calc_income_tax_considering_personalallowance(income)
    national_insurance = 0;
    if (working): 
        national_insurance = calc_national_insurance(income)    
    return income - income_tax - national_insurance


st.set_page_config(page_title = 'Pension Calculator', layout='wide', initial_sidebar_state='collapsed')

col1, col2, col3  = st.columns([1, 1, 2])

ages = [None] * 2 
salary_K = [None] * 2
employee_pension_contribution_perc = [None] * 2
employer_pension_contribution_perc = [None] * 2
starting_pension_assets_K = [None] * 2
expected_state_pension_K = [None] * 2
final_salary_pension_K = [None] * 2
retirement_age = [None] * 2
four_day_week_age = [None] * 2

with col1.expander("Person 0 details", expanded=True):
    ages[0] = int(st.text_input("Age0 (Y):", 44))
    salary_K[0] = float(st.text_input("Annual Salary0 (K):", 73))
    employer_pension_contribution_perc[0] = float(st.text_input("Employer Pension Contribution0 (%): ", 7.0))
    pension_age = int(st.text_input("State Pension Age0 (Y)", "67"))
    expected_state_pension_K[0] = float(st.text_input("State Pension0 p.a (K)", "9.3"))
    final_salary_pension_K[0] = float(st.text_input("Other Pension0 p.a (K): ", "0"))
    starting_pension_assets_K[0] = float(st.text_input("Current Pension Assets0 (K): ", "313"))

with col1.expander("Person 1 details", expanded=False):
    ages[1] = int(st.text_input("Age1 (Y):", 44))
    salary_K[1] = float(st.text_input("Annual Salary1 (K):", 15))
    employer_pension_contribution_perc[1] = float(st.text_input("Employer Pension Contribution1 (%): ", 0.0))
    pension_age = int(st.text_input("State Pension Age1 (Y)", "67"))
    expected_state_pension_K[1] = float(st.text_input("State Pension1 p.a (K)", "9.3"))
    final_salary_pension_K[1] = float(st.text_input("Other Pension1 p.a (K): ", "10.2")) # 8.4 + 1.8 (Council + RBS
    starting_pension_assets_K[1] = float(st.text_input("Current Pension Assets1 (K): ", "46"))

with col2.expander("Investment assumptions"):
    inflation = st.slider("Inflation (%): ", 2.0, 3.5, 2.5, 0.1)
    fees = st.slider("Fees (%): ", 0.4, 1.0, 0.5, 0.1)
    rate_of_return_pa_perc = st.slider("Real Return, before retirement (%): ", 0.0, 5.5, 2.5, 0.1)
    rate_of_return_after_retirement_pa_perc = st.slider("Real Return, after retirement (%): ", 1.0, 5.5, 1.5, 0.1)

for i in range(0, 2):
    with col2.expander("Person " + str(i) + " Pension Choices"):
        initial_pension_contribution = 13 if (i == 0) else int(0)
        employee_pension_contribution_perc[i] = st.slider("Employee " + str(i) + " Pension Contribution (%): " , 0, 25, initial_pension_contribution)
        retirement_age[i] = st.slider("Retirement Age "  + str(i) + " (Y):" , 45, 67, 67)
        four_day_week_age[i] = st.slider("Four Day Week Age "  + str(i) + " (Y):", 45, 67, 67)

drawdown_pa_K = col2.slider("DrawDown Amount (K): ", 15, 50, 29)
    
inflation_adjustment = inflation / 100

lowestStartingAge = min(ages[0], ages[1])
highestRetirementAge = max(retirement_age[0], retirement_age[1])

age_and_assets_at_end_of_each_year_K = []
age_and_gross_income_each_year_K = []
age_and_net_income_each_year_K = []

current_assets_K = starting_pension_assets_K[0] + starting_pension_assets_K[1];
end_of_year_total_assets_K = current_assets_K;

#
# For each year until both people are retired calculate:-
#  - net income
#  - gross income
#  - pensions assets
#
for current_age in range(lowestStartingAge, highestRetirementAge): # For each year where someone is still working
    # Apply returns from investment before adding pension contributions
    current_assets_K = current_assets_K * (1.0 + ((rate_of_return_pa_perc - fees) / 100 ))        

    yearly_gross_income_K = 0
    yearly_net_income_K = 0
    for i in range(0, 2): # For each Person 
        if (current_age < retirement_age[i]): # If still working (not still retired)
            yearly_gross_income_K += salary_K[i]

            day_adjusted_salary_K = (salary_K[i] * 0.8) if (current_age >= four_day_week_age[i]) else salary_K[i]                        

            pension_contribution_K = day_adjusted_salary_K * ((employer_pension_contribution_perc[i] + employee_pension_contribution_perc[i]) / 100)
            current_assets_K += pension_contribution_K
            
            net_salary_K = calc_income_after_tax_and_NI(True, day_adjusted_salary_K - pension_contribution_K)             
            yearly_net_income_K += net_salary_K
    
    age_and_assets_at_end_of_each_year_K.append((current_age, current_assets_K))
    age_and_gross_income_each_year_K.append((current_age, yearly_gross_income_K))
    age_and_net_income_each_year_K.append((current_age, yearly_net_income_K))

final_assets_at_retirement_K = age_and_assets_at_end_of_each_year_K[-1][1] # Final array entry, second tuple value (assets)

#
# For each year after both people are retired start drawdown and calculate:-
#  - net income
#  - gross income
#  - pensions assets
#
# Note: I'm just ignoring inflation. This is so the reported values are in today's money.
# I'd have assumed that the state pension increases with inflation, that required drawdown increases with inflation, and that then returns would include inflation (rather than exclude).
# I tested including inflation and the difference is small enough that it gave the same 'run out of money' year, so I've just left it out.
# 
state_pen_pa_K_total = expected_state_pension_K[0] + expected_state_pension_K[1]

# How many years of retirement are there with no state pension?
years_without_state_pension = pension_age - highestRetirementAge

current_age = highestRetirementAge + 1
current_assets_K = final_assets_at_retirement_K

yearly_gross_retirement_income_K = drawdown_pa_K + state_pen_pa_K_total

# Pay Tax, but not NI as we're retired. Do in two steps as each person has a tax allowance
yearly_net_retirement_income_K = \
    calc_income_after_tax_and_NI(False, (drawdown_pa_K / 2) + expected_state_pension_K[0]) + \
    calc_income_after_tax_and_NI(False, (drawdown_pa_K / 2) + expected_state_pension_K[1])    

while True:

    # Sell assets from the pension pot to live on
    current_assets_K = current_assets_K - drawdown_pa_K

    # Keep lookping until we run out of money or hit 111
    if (current_assets_K < 0 or current_age == 111):
        break

    # If we've not hit state retirement age then sell additional assets to make up the shortfall so that before/after state pension age have same income    
    if (current_age < pension_age):
        current_assets_K = current_assets_K - state_pen_pa_K_total

    # Calculate investment return on remaining assets.    
    current_assets_K = current_assets_K * (1.0 + ((rate_of_return_after_retirement_pa_perc - fees) / 100 ))
        
    age_and_assets_at_end_of_each_year_K.append((current_age, current_assets_K))
    age_and_gross_income_each_year_K.append((current_age, yearly_gross_retirement_income_K))
    age_and_net_income_each_year_K.append((current_age, yearly_net_retirement_income_K))

    current_age = current_age + 1

import altair as  alt
df = pd.DataFrame(age_and_net_income_each_year_K, columns=['Age', 'Income'])
chart_net = alt.Chart(df).mark_line().encode(
    alt.X('Age:Q', scale=alt.Scale(zero=False)),
    alt.Y('Income:Q', scale=alt.Scale(zero=False))
).properties(title="Gross & Net Income (K) vs Age")

df = pd.DataFrame(age_and_gross_income_each_year_K, columns=['Age', 'Income'])
chart_gross = alt.Chart(df).mark_line().encode(
    alt.X('Age:Q', scale=alt.Scale(zero=False)),
    alt.Y('Income:Q', scale=alt.Scale(zero=False))
).properties()

# Must be better way to add two series to single chart...
chart = alt.layer(chart_net, chart_gross)
col3.altair_chart(chart, use_container_width=True)


df = pd.DataFrame(age_and_assets_at_end_of_each_year_K, columns=['Age', 'Assets'])
chart = alt.Chart(df).mark_line().encode(
  x='Age',
  y='Assets'
).properties(title="Pension Assets (K) vs Age")

col3.altair_chart(chart, use_container_width=True)

col3.text("Assets at retire (K): " + str(int(final_assets_at_retirement_K)))
col3.text("Run out of money (Y): " + str(age_and_gross_income_each_year_K[-1][0]))
col3.text("Recommended Income Gross (K): 47.5")
col3.text("Retirement Income Gross (K): " + str(yearly_gross_retirement_income_K))
col3.text("Retirement Income Net (K): " + str(yearly_net_retirement_income_K))
