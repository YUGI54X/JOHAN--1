import os
import asyncio
import random
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TELEGRAM_TOKEN = '8734069991:AAEAzCb06GUfk-XNSg_xQy8VQiZ-IHiSy2I' # توكن البوت من BotFather
INSTA_USER = 'YOUR_INSTA_USERNAME'         # اسم حساب إنستغرام
INSTA_PASS = 'YOUR_INSTA_PASSWORD'         # كلمة سر حساب إنستغرام

# تهيئة Instaloader
L = instaloader.Instaloader(
    shortcode_to_mediaid=True,
    cache_path=None  # لتجنب تراكم الملفات المؤقتة
)

# دالة تسجيل الدخول الذكي (تستخدم الجلسة المحفوظة لتجنب الحظر)
def smart_login():
    session_file = f"session-{INSTA_USER}"
    try:
        if os.path.exists(session_file):
            L.load_session_from_file(INSTA_USER, filename=session_file)
            print("✅ تم تحميل الجلسة من الملف.")
        else:
            L.login(INSTA_USER, INSTA_PASS)
            L.save_session_to_file(filename=session_file)
            print("✅ تم تسجيل دخول جديد وحفظ الجلسة.")
    except Exception as e:
        print(f"❌ فشل تسجيل الدخول: {e}")

# دالة الترحيب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك في بوت ATOM TWO 🕵️‍♂️\n\n"
        "أرسل لي (اسم المستخدم) لأي حساب إنستغرام عام، "
        "وسأقوم بجلب الستوريات لك بشكل مخفي تماماً."
    )
    await update.message.reply_text(welcome_text)

# دالة معالجة الرسائل وجلب الستوري
async def handle_insta_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace("@", "")
    msg = await update.message.reply_text(f"⏳ جاري فحص ستوريات {username}... انتظر قليلاً")

    try:
        # إضافة تأخير بسيط لمحاكاة السلوك البشري
        await asyncio.sleep(random.randint(2, 5))
        
        # الوصول للملف الشخصي
        profile = instaloader.Profile.from_username(L.context, username)
        
        found_stories = False
        # جلب الستوريات (يتحقق من وجود ستوريات نشطة)
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                found_stories = True
                if item.is_video:
                    await update.message.reply_video(video=item.video_url, caption=f"🎥 ستوري فيديو: {username}")
                else:
                    await update.message.reply_photo(photo=item.url, caption=f"📸 ستوري صورة: {username}")
                
                # تأخير بين إرسال كل ستوري وآخر لتجنب ضغط التلغرام
                await asyncio.sleep(1)

        if not found_stories:
            await msg.edit_text(f"❌ لا توجد ستوريات عامة متاحة حالياً لحساب {username}.")
        else:
            await msg.delete() # حذف رسالة "جاري الفحص" بعد النجاح

    except instaloader.exceptions.ProfileNotExistsException:
        await msg.edit_text("❌ هذا الحساب غير موجود.")
    except instaloader.exceptions.LoginRequiredException:
        await msg.edit_text("⚠️ خطأ في تسجيل دخول البوت. يرجى مراجعة المالك.")
    except Exception as e:
        await msg.edit_text("⚠️ حدث خطأ غير متوقع. قد يكون الحساب خاصاً (Private) أو محمي.")
        print(f"Detail Error: {e}")

# الدالة الرئيسية لتشغيل البوت
def main():
    # تنفيذ تسجيل الدخول قبل بدء البوت
    smart_login()

    # بناء تطبيق التلغرام
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # إضافة الأوامر والمعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_insta_request))

    print("🚀 البوت يعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
