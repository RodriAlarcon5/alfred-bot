import asyncio
import nest_asyncio
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

nest_asyncio.apply()

# Estados
SELECCION_CIUDAD, VERIFICAR_CIUDAD = range(2)
SELECCION_CATEGORIA, RECIBIR_IMAGENES, SIGUE_O_NO = range(3, 6)

# Opciones
CIUDADES = {"1": "Ciudad de México", "2": "Guadalajara", "3": "Monterrey"}
CATEGORIAS = {
    "1": "App Naranja 🍊 – Incentivos",
    "2": "App Negra ⚫ – Incentivos",
    "3": "App Negra ⚫ – Desglose de la tarifa del usuario"
}

# chat_id del grupo
GROUP_ID = -1002642749020

# Inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = (
        "Hola, soy *Alfred* 🤖, estaré ayudándote a recibir tus screenshots. ¡Gracias por tu tiempo! 🙌\n\n"
        "Vamos a comenzar. Por favor selecciona la *ciudad donde vives* escribiendo el número correspondiente:\n\n"
        "1. Ciudad de México\n2. Guadalajara\n3. Monterrey"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return SELECCION_CIUDAD

async def guardar_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    seleccion = update.message.text.strip()
    if seleccion in CIUDADES:
        context.user_data["ciudad"] = CIUDADES[seleccion]
        await update.message.reply_text(
            f"Seleccionaste *{CIUDADES[seleccion]}*, ¿es correcto?\n\n1. Sí, es correcta\n2. No, quiero cambiarla",
            parse_mode="Markdown"
        )
        return VERIFICAR_CIUDAD
    await update.message.reply_text("Por favor escribe un número válido (1, 2 o 3).")
    return SELECCION_CIUDAD

async def verificar_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.strip() == "1":
        msg = (
            "¿Qué tipo de screenshots vas a compartir?\n\n"
            "1. App Naranja 🍊 – Incentivos\n"
            "2. App Negra ⚫ – Incentivos\n"
            "3. App Negra ⚫ – Desglose de la tarifa del usuario"
        )
        await update.message.reply_text(msg)
        return SELECCION_CATEGORIA
    elif update.message.text.strip() == "2":
        return await start(update, context)
    else:
        await update.message.reply_text("Por favor responde con 1 o 2.")
        return VERIFICAR_CIUDAD

async def guardar_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    seleccion = update.message.text.strip()
    if seleccion in CATEGORIAS:
        context.user_data["categoria"] = CATEGORIAS[seleccion]
        context.user_data["ya_enviado"] = False
        await update.message.reply_text(
            f"Excelente. Adjunta las imágenes de *{CATEGORIAS[seleccion]}*.\nEscribe *Listo* cuando termines.",
            parse_mode="Markdown"
        )
        return RECIBIR_IMAGENES
    await update.message.reply_text("Escribe 1, 2 o 3.")
    return SELECCION_CATEGORIA

async def recibir_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    categoria = context.user_data.get("categoria", "N/A")
    ciudad = context.user_data.get("ciudad", "N/A")
    fecha = update.message.date.strftime("%Y-%m-%d")

    if not context.user_data.get("ya_enviado", False):
        nombre = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = f"@{user.username}" if user.username else "(sin username)"
        mensaje_info = (
            "📤 *Nuevo set de screenshots recibido*\n\n"
            f"📅 *Fecha:* {fecha}\n"
            f"👤 *Usuario:* {nombre} ({username})\n"
            f"📍 *Ciudad:* {ciudad}\n"
            f"🗂 *Categoría:* {categoria}"
        )
        await context.bot.send_message(chat_id=GROUP_ID, text=mensaje_info, parse_mode="Markdown")
        context.user_data["ya_enviado"] = True

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=GROUP_ID, photo=file_id)
        await update.message.reply_text("Imagen recibida 👍\nPuedes enviar otra o escribe *Listo* si ya terminaste.", parse_mode="Markdown")
        return RECIBIR_IMAGENES
    elif update.message.text and update.message.text.strip().lower() == "listo":
        context.user_data["ya_enviado"] = False
        msg = (
            "¿Quieres adjuntar screenshots para otra categoría?\n\n"
            "1. Sí, otra categoría\n"
            "2. No, ya terminé"
        )
        await update.message.reply_text(msg)
        return SIGUE_O_NO
    else:
        await update.message.reply_text("Envía una imagen o escribe *Listo* si ya terminaste.", parse_mode="Markdown")
        return RECIBIR_IMAGENES

async def decidir_siguiente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    seleccion = update.message.text.strip()
    if seleccion == "1":
        msg = (
            "Perfecto. Elige otra categoría:\n\n"
            "1. App Naranja 🍊 – Incentivos\n"
            "2. App Negra ⚫ – Incentivos\n"
            "3. App Negra ⚫ – Desglose de la tarifa del usuario"
        )
        await update.message.reply_text(msg)
        return SELECCION_CATEGORIA
    elif seleccion == "2":
        await update.message.reply_text("¡Gracias por tu ayuda! Alfred ha terminado contigo. 🙌")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Por favor escribe 1 o 2.")
        return SIGUE_O_NO

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Conversación cancelada. ¡Hasta luego!")
    return ConversationHandler.END

# Iniciar bot con token desde variable de entorno
TOKEN = os.environ["BOT_TOKEN"]
app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        SELECCION_CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_ciudad)],
        VERIFICAR_CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, verificar_ciudad)],
        SELECCION_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_categoria)],
        RECIBIR_IMAGENES: [
            MessageHandler(filters.PHOTO, recibir_imagen),
            MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_imagen)
        ],
        SIGUE_O_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, decidir_siguiente)],
    },
    fallbacks=[CommandHandler("cancel", cancelar)],
)

app.add_handler(conv)

# Ejecutar
async def main():
    await app.initialize()
    await app.start()
    print("✅ Alfred está corriendo 24/7 desde Railway.")
    await app.updater.start_polling(drop_pending_updates=True)

asyncio.run(main())
