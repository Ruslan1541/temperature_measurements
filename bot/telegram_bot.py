from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import requests
from datetime import datetime
from io import BytesIO
import pytz

BOT_TOKEN = "7611352526:AAHFz0r0X_6kV9Uv5EyN-kx-WE5DuBXa3Vk"
url_temp = "http://127.0.0.1:8000/temperature/get-temperature-data/"
url_press = "http://127.0.0.1:8000/temperature/get-pressure-data/"
horizontal_delimiter = "-"

def format_temperature_data(data):
    formatted_data = []
    counter = 1
    for entry in data:
        timestamp = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        formatted_time = timestamp.astimezone(pytz.timezone('Asia/Novosibirsk')).strftime("%I:%M:%S %p")
        
        temperature = f"{round(entry['value'], 2):.2f}°"

        formatted_data.append(f"Stamp {counter}: \t {formatted_time}: \t {temperature}")
        counter += 1
    return formatted_data

def format_pressure_data(data):
    formatted_data = []
    counter = 1
    for entry in data:
        timestamp = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        formatted_time = timestamp.astimezone(pytz.timezone('Asia/Novosibirsk')).strftime("%I:%M:%S %p")
        
        pressure = f"{round(entry['value'], 2):.2f}°"

        formatted_data.append(f"Stamp {counter}: \t {formatted_time}: \t {pressure}")
        counter += 1
    return formatted_data

async def start(update, context):
    await update.message.reply_text(
        "👋 Hi there!\n\n"
        "I am a bot that fetches temperature data from your Django backend. "
        "Use /recent_temperature or /recent_pressure to see the latest readings."
        "\n\n For more information, use /help."
    )

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "Here are the commands you can use:\n\n"
        "/start - Greet the user and provide a brief introduction.\n"
        "/help - Show this help message with available commands.\n"
        "/auth <username> <password> - Authenticate using your website account credentials.\n"
        "/recent_temperature - Fetch the most recent temperature records.\n"
        "/recent_pressure - Fetch the most recent pressure records.\n"
        "/plot - Get a plot of temperature data over the last 24 hours.\n"
    )
    await update.message.reply_text(help_text)

async def auth(update: Update, context: CallbackContext):
    try:
        if len(context.args) != 2:
            await update.message.reply_text(
                "Please provide your username and password in this format:\n"
                "`/auth <username> <password>`",
                parse_mode="Markdown",
            )
            return

        username, password = context.args

        response = requests.post(
            "http://127.0.0.1:8000/account/login/",
            data={"username": username, "password": password},
            headers={"X-Telegram-Bot": "true"},
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("authenticated"):
                await update.message.reply_text("✅ Authentication successful!")
            else:
                await update.message.reply_text("❌ Invalid credentials. Please try again.")
        else:
            await update.message.reply_text("❌ Authentication failed. Please try again later.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")


async def get_plot(update: Update, context: CallbackContext):
    try:
        response = requests.get("http://127.0.0.1:8000/temperature/serve-plot/")

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.content}")

        if response.status_code == 200:
            image = BytesIO(response.content)
            await update.message.reply_photo(photo=image, caption="Here is the latest temperature and pressure plot!")
        else:
            await update.message.reply_text("Failed to fetch the plot. Please try again later.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def get_temperature(update: Update, context: CallbackContext):
    try:
        response = requests.get(url_temp)
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        if response.status_code == 200:
            data = response.json()["data"]
            if not data:
                await update.message.reply_text("No temperature data available.")
                return

            formatted_data = format_temperature_data(data[:5][::-1])
            message = f"Last 5 Temperature Records:\n {50 * horizontal_delimiter} \n" + "\n".join(formatted_data)

            await update.message.reply_text(message)
        else:
            await update.message.reply_text("Failed to fetch temperature data.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
        
async def get_pressure(update: Update, context: CallbackContext):
    try:
        response = requests.get(url_press)
        if response.status_code == 200:
            data = response.json()["data"]
            if not data:
                await update.message.reply_text("No pressure data available.")
                return

            formatted_data = format_pressure_data(data[:5][::-1])
            message = f"Last 5 Pressure Records:\n {50 * horizontal_delimiter} \n" + "\n".join(formatted_data)

            await update.message.reply_text(message)
        else:
            await update.message.reply_text("Failed to fetch temperature data.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")


def start_bot():

    application = Application.builder().token(BOT_TOKEN).build()

    
    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(CommandHandler("auth", auth))

    application.add_handler(CommandHandler("plot", get_plot))

    application.add_handler(CommandHandler("recent_temperature", get_temperature))
    
    application.add_handler(CommandHandler("recent_pressure", get_pressure))

    application.run_polling()