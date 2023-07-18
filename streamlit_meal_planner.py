import streamlit as st
import pandas as pd
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import random
import time
from data import food_items_breakfast, food_items_lunch, food_items_dinner
from prompts import pre_prompt_b, pre_prompt_l, pre_prompt_d, pre_breakfast, pre_lunch, pre_dinner, end_text, \
    example_response_l, example_response_d, negative_prompt

ANTHROPIC_API_KEY = "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"

anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

st.set_page_config(page_title="AI - Meal Planner", page_icon="🍴")

st.title("Knowledge based Meal Planner")

st.write(
    "This is a knowledge based meal planner that uses a persons information. The planner can be used to find a meal plan that satisfies the user's calorie and macronutrient requirements.")

st.write("Enter your information:")
name = st.text_input("Enter your name", value="John Doe")
age = st.number_input("Enter your age", step=1, value=20)
weight = st.number_input("Enter your weight (kg)", value=52)
height = st.number_input("Enter your height (cm)", value=170)
gender = st.radio("Choose your gender:", ["Male", "Female"])
example_response = f"This is just an example but use your creativity: You can start with, Hello {name}! I'm thrilled to be your meal planner for the day, and I've crafted a delightful and flavorful meal plan just for you. But fear not, this isn't your ordinary, run-of-the-mill meal plan. It's a culinary adventure designed to keep your taste buds excited while considering the calories you can intake. So, get ready!"


def calculate_bmr(weight, height, age, gender):
    if gender == "Male":
        bmr = 9.99 * weight + 6.25 * height - 4.92 * age + 5
    else:
        bmr = 9.99 * weight + 6.25 * height - 4.92 * age - 161

    return bmr


def get_user_preferences():
    preferences = st.multiselect("Choose your food preferences:", list(food_items_breakfast.keys()))
    return preferences


def get_user_allergies():
    allergies = st.multiselect("Choose your food allergies:", list(food_items_breakfast.keys()))
    return allergies


def generate_items_list(target_calories, food_groups):
    calories = 0
    selected_items = []
    total_items = set()
    for foods in food_groups.values():
        total_items.update(foods.keys())

    while abs(calories - target_calories) >= 10 and len(selected_items) < len(total_items):
        group = random.choice(list(food_groups.keys()))
        foods = food_groups[group]
        item = random.choice(list(foods.keys()))

        if item not in selected_items:
            cals = foods[item]
            if calories + cals <= target_calories:
                selected_items.append(item)
                calories += cals

    return selected_items, calories


def knapsack(target_calories, food_groups):
    items = []
    for group, foods in food_groups.items():
        for item, calories in foods.items():
            items.append((calories, item))

    n = len(items)
    dp = [[0 for _ in range(target_calories + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(target_calories + 1):
            value, _ = items[i - 1]

            if value > j:
                dp[i][j] = dp[i - 1][j]
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i - 1][j - value] + value)

    # Find the selected items
    selected_items = []
    j = target_calories
    for i in range(n, 0, -1):
        if dp[i][j] != dp[i - 1][j]:
            _, item = items[i - 1]
            selected_items.append(item)
            j -= items[i - 1][0]

    return selected_items, dp[n][target_calories]


bmr = calculate_bmr(weight, height, age, gender)
st.subheader(f"Your daily intake needs to have: {bmr} calories")
choose_algo = st.selectbox("Choose your algorithm", ["Random Greedy", "Knapsack"])
generate_items = st.button("Generate Meal Plan")
if generate_items:
    calories_breakfast = round((bmr * 0.5), 2)
    calories_lunch = round((bmr * (1 / 3)), 2)
    calories_dinner = round((bmr * (1 / 6)), 2)

    if choose_algo == "Random Greedy":
        meal_items_morning, cal_m = generate_items_list(calories_breakfast, food_items_breakfast)
        meal_items_lunch, cal_l = generate_items_list(calories_lunch, food_items_lunch)
        meal_items_dinner, cal_d = generate_items_list(calories_dinner, food_items_dinner)

    else:
        meal_items_morning, cal_m = knapsack(int(calories_breakfast), food_items_breakfast)
        meal_items_lunch, cal_l = knapsack(int(calories_lunch), food_items_lunch)
        meal_items_dinner, cal_d = knapsack(int(calories_dinner), food_items_dinner)
    st.header("Your Personalized Meal Plan")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("Calories for Morning: " + str(calories_breakfast))
        st.dataframe(pd.DataFrame({"Morning": meal_items_morning}))
        st.write("Total Calories: " + str(cal_m))

    with col2:
        st.write("Calories for Lunch: " + str(calories_lunch))
        st.dataframe(pd.DataFrame({"Lunch": meal_items_lunch}))
        st.write("Total Calories: " + str(cal_l))

    with col3:
        st.write("Calories for Dinner: " + str(calories_dinner))
        st.dataframe(pd.DataFrame({"Dinner": meal_items_dinner}))
        st.write("Total Calories: " + str(cal_d))

    progress_text = "You personalised meal is being generated based on the items in the basket. Please wait..."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.1)
        my_bar.progress(percent_complete + 1, text=progress_text)

    st.markdown("""---""")
    st.write("Breakfast")
    completion = anthropic.completions.create(
        model="claude-1",
        max_tokens_to_sample=2000,
        prompt=f"{HUMAN_PROMPT}{pre_prompt_b}{str(meal_items_morning)}{example_response}{pre_breakfast}{negative_prompt}{AI_PROMPT}",
    )
    out_b = completion.completion
    st.write(out_b)

    st.markdown("""---""")
    st.write("Lunch")
    completion = anthropic.completions.create(
        model="claude-1",
        max_tokens_to_sample=2000,
        prompt=f"{HUMAN_PROMPT}{pre_prompt_l}{str(meal_items_lunch)}{pre_lunch}{negative_prompt}{AI_PROMPT}",
    )
    out_l = completion.completion
    st.write(out_l)

    st.markdown("""---""")
    st.write("Dinner")
    completion = anthropic.completions.create(
        model="claude-1",
        max_tokens_to_sample=2000,
        prompt=f"{HUMAN_PROMPT}{pre_prompt_d}{str(meal_items_dinner)}{pre_dinner}{negative_prompt}{AI_PROMPT}",
    )
    out_d = completion.completion
    st.write(out_d)
    st.write(end_text)

    st.write("Thank you for using our app! We hope you enjoyed it!")