
from shiny import reactive, render
from shiny.express import ui
import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
from scipy import stats

# Font Awesome cheat sheet
from faicons import icon_svg

REFRESH_RATE = 3
MAX_DEQUE_LEN = 5
reactive_data_store = reactive.value(deque(maxlen=MAX_DEQUE_LEN))

@reactive.calc()
def generate_reactive_data():
    # Set up a refresh every REFRESH_RATE seconds
    reactive.invalidate_later(REFRESH_RATE)

    # Generate temperature and timestamp data
    temperature = round(random.uniform(-18, -16), 1)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {"temp": temperature, "timestamp": timestamp}

    # Update deque with the latest reading
    reactive_data_store.get().append(new_entry)

    # Snapshot of deque for processing
    deque_snapshot = reactive_data_store.get()

    # Convert deque to DataFrame for easier display and manipulation
    df = pd.DataFrame(deque_snapshot)

    # Retrieve the most recent data entry
    latest_entry = new_entry

    return deque_snapshot, df, latest_entry

# TITLE SECTION
ui.page_opts(title="Weather Monitor: Live Antarctic Updates", fillable=True)

# SIDEBAR SECTION
with ui.sidebar(open="open"):
    ui.h1("Antarctic Temperature Tracker", class_="text-center")
    ui.p("A real-time view of Antarctic temperature data.", class_="text-center")
    ui.hr()
    ui.h6("Additional Resources:")
    ui.a("GitHub Source", href="https://github.com/wkarto/cintel-05-cintel", target="_blank")

# MAIN CONTENT SECTION
# Layout with live data for current temperature and time
with ui.layout_columns():
    # CURRENT TEMPERATURE DISPLAY
    with ui.value_box(showcase=icon_svg("snowflake"), theme="bg-gradient-blue-purple", height=50):
        "Current Temperature"
        @render.text
        def show_temperature():
            """Display the most recent temperature reading"""
            deque_snapshot, df, latest_entry = generate_reactive_data()
            return f"{latest_entry['temp']} °C"

        "Colder Than Usual"

    # CURRENT DATE AND TIME DISPLAY
    with ui.value_box(showcase=icon_svg("clock"), theme="bg-gradient-blue-orange", height=50):
        "Current Date and Time"
        @render.text
        def show_timestamp():
            """Display the most recent timestamp"""
            deque_snapshot, df, latest_entry = generate_reactive_data()
            return f"{latest_entry['timestamp']}"

# NAVIGATION CARD
with ui.navset_card_tab(id="tab"):
    with ui.nav_panel("Live Temperature Data"):
        @render.data_frame
        def show_data_frame():
            """Display the current temperature data as a table"""
            deque_snapshot, df, latest_entry = generate_reactive_data()
            pd.set_option('display.width', None)
            return render.DataGrid(df, width="100%", height=400)

    with ui.nav_panel("Temperature Chart"):
        @render_plotly
        def plot_temperature_trend():
            # Fetch data from the reactive function
            deque_snapshot, df, latest_entry = generate_reactive_data()

            # Ensure the DataFrame contains data before plotting
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Create a line chart for the temperature data
            fig = px.line(
                df,
                x="timestamp",
                y="temp",
                title="Antarctic Temperature Trend Over Time",
                labels={"temp": "Temperature (°C)", "timestamp": "Time"},
                color_discrete_sequence=["blue"]
            )

            # Calculate the regression line
            x_vals = list(range(len(df)))
            y_vals = df["temp"]
            slope, intercept, _, _, _ = stats.linregress(x_vals, y_vals)
            df['trend_line'] = [slope * x + intercept for x in x_vals]

            # Add the regression line to the line chart
            fig.add_trace(
                px.line(
                    df, 
                    x="timestamp", 
                    y='trend_line', 
                    labels={"trend_line": "Regression Line"}
                ).data[0]
            )
            fig.data[-1].name = "Trend Line"
            fig.data[-1].line.color = "orange"
            
            # Customize the layout for better readability
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                height=300
            )

            return fig
