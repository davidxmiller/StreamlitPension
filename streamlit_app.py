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
    
def income_tax_bands_including_personalallowance(income):
    pa = 12.570
    basic_rate_end, higher_rate_end = 50.271, 150.000
    tax_free = pa if income > pa else income
    basic_rate, higher_rate, additional_rate = 0, 0, 0
    if income > pa:
        basic_rate = basic_rate_end - pa
        if income > higher_rate_end:
            higher_rate = higher_rate_end - basic_rate_end
            additional_rate = income - higher_rate_end
        elif income > basic_rate_end:
            higher_rate = income - basic_rate_end
    return tax_free, basic_rate, higher_rate, additional_rate

def calc_income_tax_considering_personalallowance(income):    
    tax_free, basic_rate, higher_rate, additional_rate = income_tax_bands_including_personalallowance(income)
    tax = (basic_rate * 0.2) + (higher_rate * 0.4) + (additional_rate * 0.45)
    return tax

def calc_income_after_tax(working, income):
    income_tax = calc_income_tax_considering_personalallowance(income)
    national_insurance = 0;
    if (working): 
        national_insurance = calc_national_insurance(income)    
    return income - income_tax - national_insurance


st.set_page_config(page_title = 'Pension Calculator', layout='wide', initial_sidebar_state='collapsed')

col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 3])

age = int(col1.text_input("Age (Y):", 44))
salary1_K = int(col1.text_input("Salary1 (K):", 73))
salary2_K = int(col1.text_input("Salary2 (K):", 15))
pen_contrib_base = float(col1.text_input("Employer Pension Contribution (%): ", 7.0))
d_pension_assets_K = int(col1.text_input("Pension1 Assets (K): ", "313"))
c_pension_assets_K= int(col1.text_input("Pension2 Assets (K): ", "46"))
pension_age = int(col1.text_input("State Pension Age (Y)", "67"))
state_pen_pa_K_1 = float(col1.text_input("State Pension1 Amount (K)", "9.3"))
state_pen_pa_K_2 = float(col1.text_input("State Pension2 Amount (K)", "9.3"))
claire_cec_pa_K = float(col1.text_input("CEC Pension Amount (K)", "8.4"))
clare_rbs_pa_K = float(col1.text_input("RBS Pension Amount (K)", "1.8"))

pen_contrib_pers= col2.slider("Employee Pension Contribution (%): ", 7, 25, 13)
inflation = col2.slider("Inflation (%): ", 2.0, 3.5, 2.5, 0.1)
fees = col2.slider("Fees (%): ", 0.4, 1.0, 0.5, 0.1)
real_return_work_pa = col2.slider("Real Return, before retirement (%): ", 0.0, 5.5, 2.5, 0.1)
real_return_retire_pa = col2.slider("Real Return, after retirement (%): ", 0.0, 5.5, 1.5, 0.1)

retire_age = col3.slider("Retirement Age (Y):", 45, 67, 67)
four_day_week_age = col3.slider("Four Day Week Age (Y):", 45, 67, 67)
drawdown_pa_K = col3.slider("DrawDown Amount (K): ", 15, 40, 28)
    
inflation_adjustment = inflation / 100
assets_K = d_pension_assets_K + c_pension_assets_K

# Calculate the assets at end of each year over [retire_in] years
assets_end_of_each_year = []
gross_income_each_year = []
income_each_year = []
assets_end_of_last_year = assets_K
pa_real_adjustment_work_in_correct_scale = 1 + (real_return_work_pa / 100)
pa_real_adjustment_retire_in_correct_scale = 1 + (real_return_retire_pa / 100) 

current_age = age

#
# Note: Until we reach retirement ignore inflation, returns are after inflation and assume salary increases with inflation    
#

pen_contrib_tot_perc_in_correct_scale = (pen_contrib_base + pen_contrib_pers) / 100

# Assume pension contributions only arrrive at end of the year (conservative)
for age in range(current_age, retire_age):
    assets_end_of_last_year = assets_end_of_last_year * pa_real_adjustment_work_in_correct_scale # Do before salary saving
    day_adjusted_salary1_K = (salary1_K * 0.8) if (age >= four_day_week_age) else salary1_K
    day_adjusted_salary2_K = (salary2_K * 0.8) if (age >= four_day_week_age) else salary2_K
    pension_contubtion = (day_adjusted_salary1_K * pen_contrib_tot_perc_in_correct_scale)
    assets_end_of_last_year = assets_end_of_last_year + pension_contubtion
    assets_end_of_each_year.append((age, assets_end_of_last_year))
    salary1_after_tax = calc_income_after_tax(True, day_adjusted_salary1_K - pension_contubtion)
    salary2_after_tax = calc_income_after_tax(True, day_adjusted_salary2_K)
    gross_income_each_year.append((age, day_adjusted_salary1_K + day_adjusted_salary2_K))
    income_each_year.append((age, salary1_after_tax + salary2_after_tax))

current_age = retire_age

# Store assets at point of retirement
final_assets_at_retirement = assets_end_of_last_year

#
# Note: Once we reach retirement assume state pension automatically increases with inflation, and that returns are after
# inflation, but assume that the amount required in draw down increased with inflation 
#

# For a couple add both state pensions together
state_pen_pa_K_total = state_pen_pa_K_1 + state_pen_pa_K_2        

# How many years of retirement are there with no state pension?
years_without_state_pension = pension_age - retire_age
    
# Calculate draw down, assume withdraw income at start of year and get stock returns at end of year (conservative)
starting_drawdown_pa_K = drawdown_pa_K
while True:
    # Take cash out
    drawdown_this_year_K = drawdown_pa_K if (current_age < pension_age) else drawdown_pa_K - state_pen_pa_K_total        
    assets = assets_end_of_last_year - drawdown_this_year_K                
    if (assets < 0 or current_age == 111):
        break
        
    # Pay fees
    assets = assets * (1 - (fees / 100));
        
    # Calculate return on remaining assets 
    assets = assets * pa_real_adjustment_retire_in_correct_scale
            
    # Increase drawdown amount required due to inflation
    drawdown_pa_K = drawdown_pa_K * (1 + inflation_adjustment)
    
    assets_end_of_each_year.append((current_age, assets))  
    assets_end_of_last_year = assets
    current_age = current_age + 1
            
# TODO:
# - Can i make a better layout? https://stackoverflow.com/questions/52980565/arranging-widgets-in-ipywidgets-interactive 

# TODO:
# - allow option to taper off working week before retirement (which can also be used to simulate lower salary)
# - maybe allow two tapers
# - remember to calculate tax
    
# TODO: Consider if/how to factor in tax 
# - our couple averagte tax rate may be lower as our income will be more balanced between us (I won't be in upper tax bracket)
# - 25% of pension withdrawls can be taken tax free (doesn't need to be single giant sum, one example providor allows 4 per year, but if was SIPP..)        

retirement_income_pa_K = \
    state_pen_pa_K_1 + \
    state_pen_pa_K_2 + \
    claire_cec_pa_K + \
    clare_rbs_pa_K +\
    starting_drawdown_pa_K;

for age in range(retire_age, current_age):
    gross_retirement_income_1 = state_pen_pa_K_1 + starting_drawdown_pa_K
    gross_retirement_income_2 = state_pen_pa_K_2 + claire_cec_pa_K + clare_rbs_pa_K
    retirement_income_1 = calc_income_after_tax(False, gross_retirement_income_1);
    retirement_income_2 = calc_income_after_tax(False, gross_retirement_income_2);
    gross_income_each_year.append((age, gross_retirement_income_1 + gross_retirement_income_2))
    income_each_year.append((age, retirement_income_1 + retirement_income_2))

col3.text("Assets at retire (K): " + str(int(final_assets_at_retirement)))
col3.text("Run out of money (Y): " + str(income_each_year[-1][0]))
col3.text("Retirement Income (K): " + str(int(income_each_year[-1][1])))
col3.text("Recommended Income (K): 47.5")

gross_income_as_perc_starting = []
starting_gross = salary1_K + salary2_K
for age, income in income_each_year:
    gross_income_as_perc_starting.append((age, income / starting_gross))


import altair as  alt
df = pd.DataFrame(income_each_year, columns=['Age', 'Income'])
chart_net = alt.Chart(df).mark_line().encode(
    alt.X('Age:Q', scale=alt.Scale(zero=False)),
    alt.Y('Income:Q', scale=alt.Scale(zero=False))
).properties(title="Gross & Net Income (K) vs Age")

df = pd.DataFrame(gross_income_each_year, columns=['Age', 'Income'])
chart_gross = alt.Chart(df).mark_line().encode(
    alt.X('Age:Q', scale=alt.Scale(zero=False)),
    alt.Y('Income:Q', scale=alt.Scale(zero=False))
).properties()

# Must be better way to add two series to single chart...
chart = alt.layer(chart_net, chart_gross)
col4.altair_chart(chart, use_container_width=True)

df = pd.DataFrame(gross_income_as_perc_starting, columns=['Age', 'Income'])
chart = alt.Chart(df).mark_line().encode(
    alt.X('Age:Q', scale=alt.Scale(zero=False)),
    alt.Y('Income:Q', scale=alt.Scale(zero=False))
).properties(title="Gross Income as % of Starting vs Age")
col4.altair_chart(chart, use_container_width=True)

df = pd.DataFrame(assets_end_of_each_year, columns=['Age', 'Assets'])
chart = alt.Chart(df).mark_line().encode(
  x='Age',
  y='Assets'
).properties(title="Pension Assets (K) vs Age")

col5.altair_chart(chart, use_container_width=True)