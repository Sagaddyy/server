"""
🤖 بوت تيليغرام - اشتراك إجباري + لوحة إدارة
==============================================
المتطلبات:
    pip install python-telegram-bot

الإعداد:
    1. ضع توكن بوتك في TELEGRAM_TOKEN
    2. ضع معرف الأدمن في ADMIN_ID
    3. تأكد أن البوت مضاف كأدمن في القناة
    4. شغّل: python bot.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember # type: ignore
from telegram.ext import ( # type: ignore
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode, ChatAction # type: ignore
from telegram.error import TelegramError # type: ignore

# ─────────────────────────────────────────────
#  ⚙️  الإعدادات
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = "8656311012:AAGHQUSQtL9uUr-trDISA1Kb6LDYqphA3U4"
ADMIN_ID       = 7145260113      # ← ضع معرف حساب الأدمن هنا (رقم)
CHANNEL_ID     = "@Tulipr1"
CHANNEL_LINK   = "https://t.me/Tulipr1"

WELCOME_MSG = (
    "هلا يحلويني  ، \n"
    "دز  ، شوي وارد 🛍"
)

# إحصائيات بسيطة في الذاكرة
stats = {
    "total_users": set(),
    "blocked_users": set(),
    "messages_count": 0,
}

# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  🔒  فحص الاشتراك في القناة
# ─────────────────────────────────────────────
async def is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        logger.info(f"User {user_id} status: {member.status}")
        return member.status in (
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        )
    except TelegramError as e:
        logger.error(f"Error checking subscription: {e}")
        return False


def subscription_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ تحققت من الاشتراك", callback_data="check_sub")],
    ])


async def ask_to_subscribe(update: Update):
    text = (
        "⚠️ *عزيزي المستخدم*\n\n"
        "يجب عليك الاشتراك في قناتنا أولاً\n"
        "قبل استخدام البوت!\n\n"
        "1️⃣ اضغط على زر الاشتراك أدناه\n"
        "2️⃣ اشترك في القناة\n"
        "3️⃣ ارجع واضغط ✅ تحققت من الاشتراك"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=subscription_keyboard()
    )


# ─────────────────────────────────────────────
#  📨  إرسال الرسائل للأدمن
# ─────────────────────────────────────────────
async def forward_to_admin(bot, user_id: int, username: str, full_name: str, message_text: str, message_id: int):
    """إرسال نسخة من رسالة المستخدم إلى الأدمن"""
    if ADMIN_ID == 0:
        return
    
    try:
        admin_text = (
            f"📨 *رسالة جديدة*\n\n"
            f"👤 *المعرف:* `{user_id}`\n"
            f"📝 *الاسم:* {full_name}\n"
            f"🆔 *اليوزر:* @{username if username else 'لا يوجد'}\n"
            f"💬 *الرسالة:*\n{message_text}"
        )
        
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✉️ رد على المستخدم", callback_data=f"reply_{user_id}_{message_id}")]
            ])
        )
    except Exception as e:
        logger.error(f"خطأ في إرسال الرسالة للأدمن: {e}")


async def send_reply_to_user(bot, user_id: int, reply_text: str):
    """إرسال رد الأدمن للمستخدم"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"📨 *رد من المشرف:*\n\n{reply_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        return True
    except Exception as e:
        logger.error(f"خطأ في إرسال الرد للمستخدم: {e}")
        return False


# ─────────────────────────────────────────────
#  🎮  أوامر المستخدم
# ─────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = user.id

    stats["total_users"].add(uid)

    # فحص حظر
    if uid in stats["blocked_users"]:
        await update.message.reply_text("🚫 أنت محظور من استخدام هذا البوت.")
        return

    # فحص الاشتراك
    if not await is_subscribed(ctx.bot, uid):
        await ask_to_subscribe(update)
        return

    # رسالة الترحيب
    await update.message.reply_text(WELCOME_MSG)
    
    # إعلام الأدمن بمستخدم جديد
    if ADMIN_ID != 0:
        try:
            await ctx.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 *مستخدم جديد*\n\n👤 المعرف: `{uid}`\n📝 الاسم: {user.full_name}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = user.id
    msg_text = update.message.text

    stats["total_users"].add(uid)
    stats["messages_count"] += 1

    # فحص حظر
    if uid in stats["blocked_users"]:
        await update.message.reply_text("🚫 أنت محظور من استخدام هذا البوت.")
        return

    # فحص الاشتراك
    if not await is_subscribed(ctx.bot, uid):
        await ask_to_subscribe(update)
        return

    # إرسال رد للمستخدم بأن رسالته وصلت
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    await update.message.reply_text(
        f"📨 تم استلام رسالتك!\nسأقوم بإرسالها للمشرف للرد عليك قريباً.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # إرسال الرسالة للأدمن
    await forward_to_admin(
        ctx.bot, 
        uid, 
        user.username, 
        user.full_name, 
        msg_text,
        update.message.message_id
    )


async def callback_check_sub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid   = query.from_user.id

    await query.answer()

    if uid in stats["blocked_users"]:
        await query.edit_message_text("🚫 أنت محظور.")
        return

    if await is_subscribed(ctx.bot, uid):
        await query.edit_message_text(
            "✅ *تم التحقق من اشتراكك بنجاح!*\n\n" + WELCOME_MSG,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            "❌ *لم يتم الاشتراك بعد!*\n\n"
            "يرجى الاشتراك في القناة أولاً ثم اضغط التحقق مجدداً.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_keyboard()
        )


# ─────────────────────────────────────────────
#  👑  لوحة الإدارة
# ─────────────────────────────────────────────
def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


def admin_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats"),
            InlineKeyboardButton("👥 المستخدمون", callback_data="adm_users"),
        ],
        [
            InlineKeyboardButton("🚫 حظر مستخدم", callback_data="adm_ban"),
            InlineKeyboardButton("✅ رفع حظر", callback_data="adm_unban"),
        ],
        [
            InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data="adm_broadcast"),
            InlineKeyboardButton("⚙️ تعديل رسالة الترحيب", callback_data="adm_setwelcome"),
        ],
        [
            InlineKeyboardButton("❌ إغلاق", callback_data="adm_close"),
        ],
    ])


async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("🚫 هذا الأمر للمشرفين فقط.")
        return

    await update.message.reply_text(
        "👑 *لوحة الإدارة*\n\nاختر ما تريد:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_menu_keyboard()
    )


async def admin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid   = query.from_user.id
    data  = query.data

    await query.answer()

    if not is_admin(uid):
        await query.edit_message_text("🚫 غير مصرح.")
        return

    # ── الرد على المستخدم
    if data.startswith("reply_"):
        parts = data.split("_")
        if len(parts) == 3:
            target_user_id = int(parts[1])
            original_msg_id = int(parts[2])
            ctx.user_data["reply_to_user"] = target_user_id
            ctx.user_data["waiting_for"] = "reply_message"
            await query.edit_message_text(
                f"✏️ اكتب الرد الذي تريد إرساله للمستخدم `{target_user_id}`:\n\n(يمكنك إلغاء الأمر بكتابة /cancel)",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_keyboard()
            )
        return

    # ── إحصائيات
    if data == "adm_stats":
        total    = len(stats["total_users"])
        blocked  = len(stats["blocked_users"])
        msgs     = stats["messages_count"]
        text = (
            "📊 *الإحصائيات*\n\n"
            f"👥 إجمالي المستخدمين: `{total}`\n"
            f"🚫 المحظورون: `{blocked}`\n"
            f"💬 الرسائل المستلمة: `{msgs}`\n"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                      reply_markup=back_keyboard())

    # ── قائمة المستخدمين
    elif data == "adm_users":
        users = list(stats["total_users"])[:30]
        if users:
            ids = "\n".join(f"• `{u}`" for u in users)
            text = f"👥 *المستخدمون* (أول 30):\n\n{ids}"
        else:
            text = "👥 لا يوجد مستخدمون بعد."
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN,
                                      reply_markup=back_keyboard())

    # ── حظر مستخدم
    elif data == "adm_ban":
        ctx.user_data["waiting_for"] = "ban_id"
        await query.edit_message_text(
            "✏️ أرسل معرف المستخدم الذي تريد حظره (رقم):",
            reply_markup=back_keyboard()
        )

    # ── رفع حظر
    elif data == "adm_unban":
        ctx.user_data["waiting_for"] = "unban_id"
        await query.edit_message_text(
            "✏️ أرسل معرف المستخدم الذي تريد رفع حظره (رقم):",
            reply_markup=back_keyboard()
        )

    # ── رسالة جماعية
    elif data == "adm_broadcast":
        ctx.user_data["waiting_for"] = "broadcast_msg"
        await query.edit_message_text(
            "📢 أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:",
            reply_markup=back_keyboard()
        )

    # ── تعديل رسالة الترحيب
    elif data == "adm_setwelcome":
        ctx.user_data["waiting_for"] = "new_welcome"
        await query.edit_message_text(
            "✏️ أرسل رسالة الترحيب الجديدة:",
            reply_markup=back_keyboard()
        )

    # ── رجوع
    elif data == "adm_back":
        ctx.user_data.pop("waiting_for", None)
        ctx.user_data.pop("reply_to_user", None)
        await query.edit_message_text(
            "👑 *لوحة الإدارة*\n\nاختر ما تريد:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_menu_keyboard()
        )

    # ── إغلاق
    elif data == "adm_close":
        await query.delete_message()


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="adm_back")]
    ])


async def handle_admin_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """معالجة مدخلات الأدمن (حظر/رفع حظر/بث/ترحيب/رد)."""
    global WELCOME_MSG
    uid  = update.effective_user.id
    text = update.message.text.strip()
    waiting = ctx.user_data.get("waiting_for")

    if not is_admin(uid) or not waiting:
        return False   # ليس مدخل أدمن

    # ── الرد على المستخدم
    if waiting == "reply_message":
        target_user_id = ctx.user_data.get("reply_to_user")
        if target_user_id:
            success = await send_reply_to_user(ctx.bot, target_user_id, text)
            if success:
                await update.message.reply_text(
                    f"✅ تم إرسال الرد للمستخدم `{target_user_id}` بنجاح.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    f"❌ فشل إرسال الرد للمستخدم `{target_user_id}`.",
                    parse_mode=ParseMode.MARKDOWN
                )
        ctx.user_data.pop("waiting_for", None)
        ctx.user_data.pop("reply_to_user", None)
        return True

    ctx.user_data.pop("waiting_for")

    # حظر
    if waiting == "ban_id":
        try:
            target = int(text)
            stats["blocked_users"].add(target)
            await update.message.reply_text(
                f"✅ تم حظر المستخدم `{target}` بنجاح.",
                parse_mode=ParseMode.MARKDOWN
            )
        except ValueError:
            await update.message.reply_text("❌ معرف غير صحيح. أرسل رقماً فقط.")

    # رفع حظر
    elif waiting == "unban_id":
        try:
            target = int(text)
            stats["blocked_users"].discard(target)
            await update.message.reply_text(
                f"✅ تم رفع حظر المستخدم `{target}` بنجاح.",
                parse_mode=ParseMode.MARKDOWN
            )
        except ValueError:
            await update.message.reply_text("❌ معرف غير صحيح.")

    # رسالة جماعية
    elif waiting == "broadcast_msg":
        sent = failed = 0
        for user_id in list(stats["total_users"]):
            try:
                await ctx.bot.send_message(chat_id=user_id, text=text)
                sent += 1
            except Exception:
                failed += 1
        await update.message.reply_text(
            f"📢 *نتيجة الإرسال الجماعي*\n\n"
            f"✅ نجح: `{sent}`\n"
            f"❌ فشل: `{failed}`",
            parse_mode=ParseMode.MARKDOWN
        )

    # تعديل رسالة الترحيب
    elif waiting == "new_welcome":
        WELCOME_MSG = text
        await update.message.reply_text(
            "✅ تم تحديث رسالة الترحيب بنجاح!\n\n"
            f"الرسالة الجديدة:\n{WELCOME_MSG}"
        )

    return True


async def handle_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية"""
    uid = update.effective_user.id
    if is_admin(uid) and ctx.user_data.get("waiting_for"):
        ctx.user_data.clear()
        await update.message.reply_text("✅ تم إلغاء العملية الحالية.")
    else:
        await update.message.reply_text("لا توجد عملية نشطة للإلغاء.")


async def handle_all_messages(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """نقطة التحكم الرئيسية للرسائل."""
    # تحقق من مدخلات الأدمن أولاً
    if await handle_admin_input(update, ctx):
        return
    # ثم معالجة رسائل المستخدمين
    await handle_message(update, ctx)


# ─────────────────────────────────────────────
#  🚀  التشغيل
# ─────────────────────────────────────────────
def main():
    if ADMIN_ID == 0:
        logger.warning("⚠️  لم تقم بتعيين ADMIN_ID! الإدارة لن تعمل.")

    logger.info("🚀 جاري تشغيل البوت...")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # أوامر
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("cancel", handle_cancel))

    # Callbacks
    app.add_handler(CallbackQueryHandler(callback_check_sub, pattern="^check_sub$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(adm_|reply_)"))

    # رسائل نصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    logger.info("✅ البوت يعمل! اضغط Ctrl+C للإيقاف.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()