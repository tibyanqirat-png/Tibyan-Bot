import os
import json
from telegram import (
    Update,
    ChatJoinRequest,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    TypeHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8530689522

DATA_FILE = "registration_data.json"
JOIN_REQUESTS_FILE = "join_requests.json"

MALE_START = 450
FEMALE_START = 1450

QIRAAT_GROUP = "https://t.me/+hV1SdDU2RPVmNGQ0"
MALE_GROUP = "https://t.me/+R1glQTVbUW44OTBk"
FEMALE_GROUP = "https://t.me/+1PLSYSbaRW1iZGE0"

FINAL_ACCOUNT = "@tibyankitab"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"male_next": MALE_START, "female_next": FEMALE_START}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"male_next": MALE_START, "female_next": FEMALE_START}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("ለመመዝገብ")]]

    await update.message.reply_text(
        "ሰላም! 👋\n\n"
        "እንኳን ወደ ቲብያን መድረሳ በደህና መጡ።",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        ),
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        'እባክዎ ሙሉ ስምዎን ይጻፉ (ቢያንስ ሁለት ቃላት መሆን አለበት፣ ለምሳሌ: "ሙሐመድ አሕመድ")',
        reply_markup=ReplyKeyboardRemove(),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Registration button
    if text == "ለመመዝገብ":
        await register(update, context)
        return

    # Name
    if "name" not in context.user_data:
        if len(text.split()) < 2:
            await update.message.reply_text(
                "❌ ትክክል ያልሆነ መልስ አስገብተዋል። "
                "እባክዎ ቢያንስ ሁለት ቃላት (የመጀመሪያ እና የአባት ስም) "
                "ያካተተ ሙሉ ስምዎን ያስገቡ።"
            )
            return

        context.user_data["name"] = text

        keyboard = [
            [
                InlineKeyboardButton("ወንድ", callback_data="gender_male"),
                InlineKeyboardButton("ሴት", callback_data="gender_female"),
            ]
        ]

        await update.message.reply_text(
            f"ስም: {text}\n\n"
            "2️⃣ ፆታዎን ይምረጡ።",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return


async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    gender_value = "ወንድ" if query.data == "gender_male" else "ሴት"
    context.user_data["gender"] = gender_value

    keyboard = [[
        KeyboardButton("📱 ስልኬን አጋራ", request_contact=True)
    ]]

    await query.message.reply_text(
        f"ስም: {context.user_data['name']}\n"
        f"ፆታ: {gender_value}\n\n"
        "3️⃣ እባክዎ የስልክ ቁጥርዎን ያጋሩ።",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        ),
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact

    context.user_data["phone"] = contact.phone_number

    name = context.user_data["name"]
    gender_value = context.user_data["gender"]
    phone = contact.phone_number

    keyboard = [[
        InlineKeyboardButton("ትክክል ነው", callback_data="confirm_yes"),
        InlineKeyboardButton("ከእንደገና ተመዝገብ", callback_data="confirm_no"),
    ]]

    await update.message.reply_text(
        f"ስም: {name}\n"
        f"ፆታ: {gender_value}\n"
        f"ስልክ: {phone}\n\n"
        "ከላይ የተቀመጠው መረጃ ትክክል መሆኑን ያረጋግጡ\n"
        "ያረጋግጡ።",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_no":
        context.user_data.clear()

        await query.message.reply_text(
            'እባክዎ ሙሉ ስምዎን ይጻፉ (ቢያንስ ሁለት ቃላት መሆን አለበት፣ ለምሳሌ: "ሙሐመድ አሕመድ")',
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    keyboard = [[
        InlineKeyboardButton("ቀጣይ", callback_data="qiraat_next")
    ]]

    await query.message.reply_text(
        "ምዝገባዎ በተሳካ ሁኔታ ተጠናቋል።\n\n"
        "ከታች ባለው ሊንክ ወደ ቂርኣት ግሩፕ ለመግባት Request አድርጉ። "
        "በመቀጠል ቀጣይ የሚለውን ቁልፍ ተጫኑ።\n\n"
        f"{QIRAAT_GROUP}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request

    if not request:
        return

    if context.user_data.get("awaiting_murajaa_request"):
        context.user_data["murajaa_requested"] = True
    else:
        context.user_data["qiraat_requested"] = True
        
async def qiraat_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not context.user_data.get("qiraat_requested"):
        await query.message.reply_text(
            "❌ እባክዎ መጀመሪያ የቂርኣት ግሩፑን Request አድርጉ።\n\n"
            "Request ካደረጉ በኋላ ይህን ቁልፍ እንደገና ይጫኑ።"
        )
        return

    context.user_data["awaiting_murajaa_request"] = True

    gender_value = context.user_data.get("gender")

    if gender_value == "ወንድ":
        text = (
            "በመቀጠል የወንድሞች የሙራጀዓ ግሩፕን ለመቀላቀል "
            "ከታች ባለው ሊንክ request አድርጉ። "
            "ከዛም ቀጣይ የሚለውን ቁልፍ ተጫኑ።\n\n"
            f"{MALE_GROUP}"
        )
    else:
        text = (
            "በመቀጠል የእህቶች የሙራጀዓ ግሩፕን ለመቀላቀል "
            "ከታች ባለው ሊንክ request አድርጉ። "
            "ከዛም ቀጣይ የሚለውን ቁልፍ ተጫኑ።\n\n"
            f"{FEMALE_GROUP}"
        )

    keyboard = [[
        InlineKeyboardButton("ቀጣይ", callback_data="murajaa_next")
    ]]

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def murajaa_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not context.user_data.get("murajaa_requested"):
        await query.message.reply_text(
            "❌ እባክዎ መጀመሪያ የሙራጀዓ ግሩፑን Request አድርጉ።\n\n"
            "Request ካደረጉ በኋላ ይህን ቁልፍ እንደገና ይጫኑ።"
        )
        return

    data = load_data()

    if context.user_data["gender"] == "ወንድ":
        number = data["male_next"]
        code = f"M{number}"
        data["male_next"] += 1
    else:
        number = data["female_next"]
        code = f"F{number}"
        data["female_next"] += 1

    save_data(data)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"ሙሉ ስም: {context.user_data['name']}\n"
            f"የምዝገባ ኮድ: {code}\n"
            f"ፆታ: {context.user_data['gender']}\n"
            f"ስልክ ቁጥር: {context.user_data['phone']}"
        )
    )

    await query.message.reply_text(
        f"የምዝገባ ቁጥራችሁ፦\n\n"
        f"<code>{code}</code>\n\n"
        f"ይህ የምዝገባ ቁጥራችሁ ነው {FINAL_ACCOUNT} ላይ "
        "ኮዳችሁን በመላክ ምዝገባችሁን አጠናቁ።\n\n"
        "መልካም የቂርኣት ጊዜ።",
        parse_mode="HTML",
    )
def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is missing!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(gender, pattern="^gender_"))
    app.add_handler(CallbackQueryHandler(confirmation, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(qiraat_next, pattern="^qiraat_next$"))
    app.add_handler(CallbackQueryHandler(murajaa_next, pattern="^murajaa_next$"))
    app.add_handler(TypeHandler(Update, handle_join_request), group=1)

    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
