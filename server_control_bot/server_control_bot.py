import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram.request import HTTPXRequest
import os

# Telegram bot token (set your bot token here)
BOT_TOKEN = ""

# Base directory prefix for all paths (set your own base directory, e.g. "/mnt/storage")
BASE_DIRECTORY = ""

# Filesystem / device path for free-space checks (set your own, e.g. "/dev/md5" or mount point)
DISK_PATH = ""

# HTTPXRequest timeouts for Telegram API
request = HTTPXRequest(
    read_timeout=60,
    connect_timeout=60,
)

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000  # Maximum length of a message we send back

# Allowed Telegram user IDs (set your own IDs here)
ALLOWED_USERS = set()  # Example: {123456789, 987654321}


def check_access(user_id: int) -> bool:
    """
    Check if a given Telegram user_id is allowed to use this bot.
    """
    return user_id in ALLOWED_USERS


# /start command
async def start(update: Update, context):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("❌ You are not allowed to use this bot.")
        return

    await update.message.reply_text("Hello! Use the commands to run server scripts.")
    await update.message.reply_text(f"Your user_id: {user_id}")


# /dirspace command: check folder size relative to BASE_DIRECTORY
async def dirspace(update: Update, context):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("❌ You are not allowed to use this command.")
        return

    if not update.message:
        logger.error("Error: message object is missing in update")
        return

    if len(context.args) == 0:
        await update.message.reply_text(
            f"Please provide the folder path relative to '{BASE_DIRECTORY}'. "
            f"Example: /dirspace folder/subfolder"
        )
        return

    relative_path = " ".join(context.args)
    folder_path = os.path.join(BASE_DIRECTORY, relative_path)

    if not os.path.exists(folder_path):
        await update.message.reply_text(
            f"❌ Path '{folder_path}' does not exist. Please check the path."
        )
        return

    if not os.path.isdir(folder_path):
        await update.message.reply_text(
            f"❌ '{folder_path}' is not a directory. Please provide a valid folder path."
        )
        return

    message = await update.message.reply_text(
        f"Checking folder size: {folder_path}..."
    )

    try:
        process = await asyncio.create_subprocess_exec(
            "du",
            "-sh",
            folder_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        stdout_text = stdout.decode() if stdout else "No output"
        stderr_text = stderr.decode() if stderr else "No errors"

        if process.returncode == 0:
            await message.edit_text(
                f"✅ Folder size for {folder_path}:\n\n{stdout_text}"
            )
        else:
            await message.edit_text(
                f"❌ Error while running 'du':\n{stderr_text}"
            )

    except Exception as e:
        await message.edit_text(
            f"❌ An exception occurred while running 'du': {e}"
        )


# Progress animation for long-running operations
async def show_progress(message, stop_event: asyncio.Event):
    progress_patterns = ["⏳ Running.", "⏳ Running..", "⏳ Running..."]
    i = 0
    while not stop_event.is_set():
        try:
            await message.edit_text(progress_patterns[i % len(progress_patterns)])
        except Exception as e:
            logger.warning(f"Failed to update progress message: {e}")
            break
        i += 1
        await asyncio.sleep(3)


# Generic async script runner
async def run_script(update: Update, context, script_name: str):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("❌ You are not allowed to use this command.")
        return

    message = await update.message.reply_text(
        f"Starting script: {script_name}..."
    )

    stop_event = asyncio.Event()
    task = asyncio.create_task(show_progress(message, stop_event))

    try:
        process = await asyncio.create_subprocess_exec(
            "python3",
            script_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        stop_event.set()
        await task

        stdout_text = stdout.decode()[:MAX_MESSAGE_LENGTH] if stdout else "No output"
        stderr_text = stderr.decode()[:MAX_MESSAGE_LENGTH] if stderr else "No errors"

        if process.returncode == 0:
            await message.edit_text(
                f"✅ Script {script_name} finished successfully!"
            )
            if stdout_text and stdout_text != "No output":
                await update.message.reply_text(
                    f"Output (truncated to {MAX_MESSAGE_LENGTH} chars):\n{stdout_text}"
                )
        else:
            await message.edit_text(
                f"❌ Error while running script {script_name}:\n{stderr_text}"
            )

    except Exception as e:
        stop_event.set()
        await task
        await message.edit_text(
            f"❌ An exception occurred while starting script {script_name}: {e}"
        )


# /freespace command: check free space on DISK_PATH or mount
async def freespace(update: Update, context):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("❌ You are not allowed to use this command.")
        return

    if not DISK_PATH:
        await update.message.reply_text(
            "DISK_PATH is not configured. Please set DISK_PATH in the bot configuration."
        )
        return

    message = await update.message.reply_text(
        f"Checking free space on {DISK_PATH}..."
    )

    try:
        process = await asyncio.create_subprocess_exec(
            "df",
            "-h",
            DISK_PATH,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        stdout_text = stdout.decode() if stdout else "No output"
        stderr_text = stderr.decode() if stderr else "No errors"

        if process.returncode == 0:
            await message.edit_text(
                f"✅ Free space on {DISK_PATH}:\n\n{stdout_text}"
            )
        else:
            await message.edit_text(
                f"❌ Error while running 'df':\n{stderr_text}"
            )

    except Exception as e:
        await message.edit_text(
            f"❌ An exception occurred while running 'df': {e}"
        )


# Specific commands mapped to concrete scripts (replace with your own script names if needed)
async def kanjian(update: Update, context):
    await run_script(update, context, "KNJ2DMB_0.py")


async def spotify(update: Update, context):
    await run_script(update, context, "BR2DMBspotify.py")


async def youtubeid(update: Update, context):
    await run_script(update, context, "BR2DMByoutubeid.py")


async def youtubeonly(update: Update, context):
    await run_script(update, context, "BR2DMByoutubeonly.py")


async def ddex(update: Update, context):
    await run_script(update, context, "BR2DMB1-4.py")


# Entry point
if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.warning("BOT_TOKEN is empty. Please set your bot token before running.")
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .request(request)
        .build()
    )

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("kanjian", kanjian))
    application.add_handler(CommandHandler("spotify", spotify))
    application.add_handler(CommandHandler("youtubeid", youtubeid))
    application.add_handler(CommandHandler("youtubeonly", youtubeonly))
    application.add_handler(CommandHandler("ddex", ddex))
    application.add_handler(CommandHandler("freespace", freespace))
    application.add_handler(CommandHandler("dirspace", dirspace))

    logger.info("Bot started...")
    application.run_polling()