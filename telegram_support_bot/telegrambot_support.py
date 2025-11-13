import logging
import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING, TYPING_DELETION, TYPING_PROFILE, TYPING_OTHER, TYPING_ATTACH = range(5)

# Manager Telegram user ID (set to your manager's chat ID)
MANAGER_ID = 0  # TODO: replace with real manager chat ID

# Initialize SQLite database
conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    codes TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    requester_id INTEGER NOT NULL
)
"""
)
conn.commit()

# Migrate existing table to include requester_id if missing
cursor.execute("PRAGMA table_info(tasks)")
columns = [row[1] for row in cursor.fetchall()]
if "requester_id" not in columns:
    cursor.execute(
        "ALTER TABLE tasks ADD COLUMN requester_id INTEGER NOT NULL DEFAULT 0"
    )
    conn.commit()

# Migrate existing table to include rejection_reason if missing
cursor.execute("PRAGMA table_info(tasks)")
columns = [row[1] for row in cursor.fetchall()]
if "rejection_reason" not in columns:
    cursor.execute("ALTER TABLE tasks ADD COLUMN rejection_reason TEXT")
    conn.commit()

# Migrate existing table to include username if missing
cursor.execute("PRAGMA table_info(tasks)")
columns = [row[1] for row in cursor.fetchall()]
if "username" not in columns:
    cursor.execute("ALTER TABLE tasks ADD COLUMN username TEXT")
    conn.commit()

# Migrate existing table to include attachments if missing
cursor.execute("PRAGMA table_info(tasks)")
columns = [row[1] for row in cursor.fetchall()]
if "attachments" not in columns:
    cursor.execute("ALTER TABLE tasks ADD COLUMN attachments TEXT")
    conn.commit()


# /start command: present options
async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Delete releases", callback_data="delete")],
        [InlineKeyboardButton("Profile edits", callback_data="profile")],
        [InlineKeyboardButton("Other", callback_data="other")],
    ]
    await update.message.reply_text(
        "Choose the type of request:", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING


# Handle button presses
async def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "delete":
        await query.edit_message_text(
            "Enter the list of UPC/EAN codes, one per line."
        )
        return TYPING_DELETION
    elif query.data == "other":
        await query.edit_message_text(
            "First, describe the issue in free form (if needed).\nFile upload will be a separate step."
        )
        return TYPING_OTHER
    else:
        await query.edit_message_text(
            "First enter the UPC/EAN codes (space- or line-separated) and the task description.\nFile upload will be a separate step."
        )
        return TYPING_PROFILE


# Handle deletions
async def received_deletion(update: Update, context: CallbackContext) -> int:
    codes = [c.strip() for c in update.message.text.split() if c.strip()]
    codes_str = "\n".join(codes)
    cursor.execute(
        "INSERT INTO tasks (type, codes, description, requester_id, username) VALUES (?, ?, ?, ?, ?)",
        (
            "deletion",
            codes_str,
            None,
            update.effective_user.id,
            update.effective_user.username,
        ),
    )
    task_id = cursor.lastrowid
    conn.commit()
    # Prepare content
    content = f"Codes:\n{codes_str}"
    await update.message.reply_text(
        f"Delete request saved (ID {task_id}).\n{content}"
    )
    await notify_manager(task_id)
    return ConversationHandler.END


# Handle profile text entry, then ask for attachments
async def handle_profile_text(update: Update, context: CallbackContext) -> int:
    # Parse codes and description similarly to received_profile
    raw_text = update.message.text or update.message.caption or ""
    text = raw_text.strip()
    lines = text.splitlines()
    codes = []
    desc_lines = []
    codes_collected = False
    for line in lines:
        if not codes_collected and (line.replace(" ", "").isalnum() and len(line) >= 8):
            codes.append(line.strip())
        else:
            codes_collected = True
            desc_lines.append(line)
    codes_str = "\n".join(codes)
    desc_str = "\n".join(desc_lines)
    # Store pending task data
    context.user_data["task_data"] = {
        "type": "profile",
        "codes": codes_str,
        "description": desc_str,
        "requester_id": update.effective_user.id,
        "username": update.effective_user.username,
    }
    # Prompt for attachments
    keyboard = [
        [
            InlineKeyboardButton(
                "Submit without files", callback_data="skip_attach"
            )
        ]
    ]
    reply = await update.message.reply_text(
        "Now attach files (jpg, png, audio) or click the button below to submit without files.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.user_data["prompt_message_id"] = reply.message_id
    return TYPING_ATTACH


# Handle other text entry, then ask for attachments
async def handle_other_text(update: Update, context: CallbackContext) -> int:
    raw_desc = update.message.text or update.message.caption or ""
    desc = raw_desc.strip()
    context.user_data["task_data"] = {
        "type": "other",
        "codes": "",
        "description": desc,
        "requester_id": update.effective_user.id,
        "username": update.effective_user.username,
    }
    keyboard = [
        [
            InlineKeyboardButton(
                "Submit without files", callback_data="skip_attach"
            )
        ]
    ]
    reply = await update.message.reply_text(
        "Now attach files (jpg, png, audio) or click the button below to submit without files.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.user_data["prompt_message_id"] = reply.message_id
    return TYPING_ATTACH


# Skip attachment step and save task without files
async def skip_attachments(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    # Delete attachment prompt
    await update.callback_query.message.delete()
    data = context.user_data.pop("task_data")
    cursor.execute(
        "INSERT INTO tasks (type, codes, description, requester_id, username, attachments) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data["type"],
            data["codes"],
            data["description"],
            data["requester_id"],
            data["username"],
            None,
        ),
    )
    task_id = cursor.lastrowid
    conn.commit()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Your request #{task_id} has been sent to the manager and is pending.",
    )
    await notify_manager(task_id)


# Handle attachments then save task
async def handle_attachments(update: Update, context: CallbackContext) -> int:
    # Delete attachment prompt
    prompt_id = context.user_data.pop("prompt_message_id", None)
    if prompt_id:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=prompt_id
        )
    attachments = []
    if update.message.document:
        attachments.append(f"{update.message.document.file_id}|document")
    if update.message.photo:
        attachments.append(f"{update.message.photo[-1].file_id}|photo")
    if update.message.audio:
        attachments.append(f"{update.message.audio.file_id}|audio")
    if update.message.voice:
        attachments.append(f"{update.message.voice.file_id}|voice")
    attachments_str = ",".join(attachments) if attachments else None
    data = context.user_data.pop("task_data")
    cursor.execute(
        "INSERT INTO tasks (type, codes, description, requester_id, username, attachments) VALUES (?, ?, ?, ?, ?, ?)",
        (
            data["type"],
            data["codes"],
            data["description"],
            data["requester_id"],
            data["username"],
            attachments_str,
        ),
    )
    task_id = cursor.lastrowid
    conn.commit()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Your request #{task_id} has been sent to the manager and is pending.",
    )
    await notify_manager(task_id)
    return ConversationHandler.END


# Notify manager about a new task
async def notify_manager(task_id: int) -> None:
    cursor.execute(
        "SELECT type, codes, description, requester_id, username, attachments FROM tasks WHERE id = ?",
        (task_id,),
    )
    ttype, codes, description, requester_id, username, attachments_str = (
        cursor.fetchone()
    )
    # Include requester ID and username in header
    header = f"New task #{task_id} from {requester_id}"
    if username:
        header += f" / @{username}"
    text = f"{header}\nType: {ttype}\nCodes:\n{codes}"
    if description:
        text += f"\nDescription:\n{description}"
    text += "\n\nMark as completed:"
    keyboard = [
        [
            InlineKeyboardButton(
                "Done without comment ✅", callback_data=f"done_{task_id}"
            ),
            InlineKeyboardButton(
                "With comment ✍️", callback_data=f"done_comment_{task_id}"
            ),
        ],
        [InlineKeyboardButton("Reject ❌", callback_data=f"reject_{task_id}")],
    ]
    await application.bot.send_message(
        chat_id=MANAGER_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    # Send attachments if any
    if attachments_str:
        for entry in attachments_str.split(","):
            file_id, ftype = entry.split("|")
            if ftype == "document":
                await application.bot.send_document(
                    chat_id=MANAGER_ID, document=file_id
                )
            elif ftype == "photo":
                await application.bot.send_photo(
                    chat_id=MANAGER_ID, photo=file_id
                )
            elif ftype == "audio":
                await application.bot.send_audio(
                    chat_id=MANAGER_ID, audio=file_id
                )
            elif ftype == "voice":
                await application.bot.send_voice(
                    chat_id=MANAGER_ID, voice=file_id
                )


# Manager marks a task done without comment
async def simple_done_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    # Mark task done
    cursor.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
    conn.commit()
    # Notify requester
    cursor.execute("SELECT requester_id FROM tasks WHERE id = ?", (task_id,))
    requester_id = cursor.fetchone()[0]
    await context.bot.send_message(
        chat_id=requester_id,
        text=f"Your request #{task_id} has been completed. ✅",
        disable_notification=True,
    )
    await query.edit_message_text(
        f"Task #{task_id} has been marked as completed. ✅"
    )


# Manager begins done-with-comment flow
async def begin_done_comment_callback(
    update: Update, context: CallbackContext
) -> None:
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[2])
    context.user_data["done_task_id"] = task_id
    await query.edit_message_text(
        f"Enter a comment for the user for task #{task_id}:"
    )


# Manager lists tasks
async def list_tasks(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != MANAGER_ID:
        await update.message.reply_text("Access denied.")
        return
    # Detailed view if an ID is provided: /tasks <ID>
    if context.args:
        try:
            task_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                f"Invalid ID: {context.args[0]}"
            )
            return
        cursor.execute(
            "SELECT id, type, codes, description, status, requester_id, username, rejection_reason FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            await update.message.reply_text(f"Task #{task_id} not found.")
            return
        (
            id_,
            ttype,
            codes,
            description,
            status,
            requester_id,
            username,
            rejection_reason,
        ) = row
        text = (
            f"Task #{id_}\nStatus: {status}\nType: {ttype}\nCodes:\n{codes}"
        )
        if description:
            text += f"\nDescription:\n{description}"
        text += f"\nSubmitted by: {requester_id}"
        if username:
            text += f" / @{username}"
        if status == "rejected" and rejection_reason:
            text += f"\nRejection reason:\n{rejection_reason}"
        await update.message.reply_text(text)
        return
    cursor.execute(
        "SELECT id, type, status, requester_id, username FROM tasks ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    text = "Task list:\n"
    for row in rows:
        task_id, ttype, status, requester_id, username = row
        user_info = f"{requester_id}"
        if username:
            user_info += f" / @{username}"
        text += f"ID {task_id}: {ttype} — {status} (from {user_info})\n"
    await update.message.reply_text(text)


# Cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


# Handle manager clicking "Reject"
async def reject_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    task_id = int(data.split("_")[1])
    # Ask manager for rejection reason
    await query.edit_message_text(
        f"Enter rejection reason for task #{task_id}:"
    )
    # Store awaiting state
    context.user_data["reject_task_id"] = task_id


# Unified handler for manager text replies on approval or rejection
async def handle_manager_text(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != MANAGER_ID:
        return
    # Rejection flow
    if "reject_task_id" in context.user_data:
        task_id = context.user_data.pop("reject_task_id")
        reason = update.message.text.strip()
        cursor.execute(
            "UPDATE tasks SET status = 'rejected', rejection_reason = ? WHERE id = ?",
            (reason, task_id),
        )
        conn.commit()
        cursor.execute(
            "SELECT requester_id FROM tasks WHERE id = ?", (task_id,)
        )
        requester_id = cursor.fetchone()[0]
        await context.bot.send_message(
            chat_id=requester_id,
            text=f"Your request #{task_id} was rejected. ❌\nReason: {reason}",
            disable_notification=True,
        )
        await update.message.reply_text(
            f"Task #{task_id} rejected with reason. ❌"
        )
        return
    # Approval with comment flow
    if "done_task_id" in context.user_data:
        task_id = context.user_data.pop("done_task_id")
        comment = update.message.text.strip()
        cursor.execute(
            "UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,)
        )
        conn.commit()
        cursor.execute(
            "SELECT requester_id FROM tasks WHERE id = ?", (task_id,)
        )
        requester_id = cursor.fetchone()[0]
        text = f"Your request #{task_id} has been completed. ✅"
        if comment:
            text += f"\n{comment}"
        await context.bot.send_message(
            chat_id=requester_id,
            text=text,
            disable_notification=True,
        )
        await update.message.reply_text(
            f"Task #{task_id} has been marked as completed. ✅"
        )


# Command to resend notification for pending task
async def resend_notification(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != MANAGER_ID:
        await update.message.reply_text("Access denied.")
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /resend <task ID>"
        )
        return
    try:
        task_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            f"Invalid ID: {context.args[0]}"
        )
        return
    cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text(
            f"Task #{task_id} not found."
        )
        return
    status = row[0]
    if status != "pending":
        await update.message.reply_text(
            f"Cannot resend: task status is {status}."
        )
        return
    await update.message.reply_text(
        f"Resending notification for task #{task_id}..."
    )
    await notify_manager(task_id)


# Set bot command menus for users and manager
async def set_bot_commands(application):
    # Global commands for all users
    await application.bot.set_my_commands(
        [BotCommand("start", "Start bot")],
        scope=BotCommandScopeDefault(),
    )
    # Additional commands for manager
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Start bot"),
            BotCommand("tasks", "Task list or /tasks <ID>"),
            BotCommand("resend", "Resend notification"),
        ],
        scope=BotCommandScopeChat(chat_id=MANAGER_ID),
    )


# Main function
def main() -> None:
    global application
    TOKEN = ""  # TODO: set your bot token here
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(set_bot_commands)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        allow_reentry=True,
        states={
            CHOOSING: [CallbackQueryHandler(button)],
            TYPING_DELETION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, received_deletion
                )
            ],
            TYPING_PROFILE: [
                MessageHandler(~filters.COMMAND, handle_profile_text)
            ],
            TYPING_OTHER: [
                MessageHandler(~filters.COMMAND, handle_other_text)
            ],
            TYPING_ATTACH: [
                MessageHandler(~filters.COMMAND, handle_attachments),
                CallbackQueryHandler(
                    skip_attachments, pattern=r"^skip_attach$"
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(
        CallbackQueryHandler(
            simple_done_callback, pattern=r"^done_[0-9]+$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            begin_done_comment_callback,
            pattern=r"^done_comment_[0-9]+$",
        )
    )
    application.add_handler(CommandHandler("tasks", list_tasks))

    # Handler for /resend command
    application.add_handler(CommandHandler("resend", resend_notification))

    # Handler for task rejection callback
    application.add_handler(
        CallbackQueryHandler(reject_callback, pattern=r"^reject_")
    )

    # Unified handler for manager text replies
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.User(user_id=MANAGER_ID),
            handle_manager_text,
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()