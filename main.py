import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

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

# ID del grupo
GROUP_ID = int(os.getenv("GROUP_ID", "-1002642749020"))

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hola, soy Alfred 🤖\nSelecciona tu ciudad:\n"
        "1. Ciudad de México\n2. Guadalajara\n3. Monterrey"
    )
    return SELECCION_CIUDAD

async def guardar_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    if texto not in CIUDADES:
        await update.message.reply_text("Selecciona una opción válida: 1, 2 o 3.")
        return SELECCION_CIUDAD
    context.user_data["ciudad"] = CIUDADES[texto]
    await update.message.reply_text(f"Seleccionaste {CIUDADES[texto]}.\nEscribe tu nombre:")
    return VERIFICAR_CIUDAD

async def verificar_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text(
        "Selecciona la categoría:\n"
        "1. App Naranja 🍊 – Incentivos\n"
        "2. App Negra ⚫ – Incentivos\n"
        "3. App Negra ⚫ – Desglose de la tarifa del usuario"
    )
    return SELECCION_CATEGORIA

async def guardar_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    if texto not in CATEGORIAS:
        await update.message.reply_text("Selecciona una opción válida: 1, 2 o 3.")
        return SELECCION_CATEGORIA
    context.user_data["categoria"] = CATEGORIAS[texto]
    await update.message.reply_text("Ahora envíame una o más capturas. Cuando termines escribe 'listo'.")
    return RECIBIR_IMAGENES

async def recibir_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.lower() == "listo":
        await update.message.reply_text("¿Quieres subir otra categoría? (sí/no)")
        return SIGUE_O_NO

    if update.message.photo:
        largest_photo = update.message.photo[-1]
        caption = f"{context.user_data['nombre']}\n{context.user_data['ciudad']}\n{context.user_data['categoria']}"
        await context.bot.send_photo(
            chat_id=GROUP_ID,
            photo=largest_photo.file_id,
            caption=caption
        )
        await update.message.reply_text("📸 Imagen recibida.")
    else:
        await update.message.reply_text("Envía una imagen o escribe 'listo' si ya terminaste.")
    return RECIBIR_IMAGENES

async def decidir_siguiente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.strip().lower()
    if respuesta == "sí":
        await update.message.reply_text(
            "Selecciona la categoría:\n"
            "1. App Naranja 🍊 – Incentivos\n"
            "2. App Negra ⚫ – Incentivos\n"
            "3. App Negra ⚫ – Desglose de la tarifa del usuario"
        )
        return SELECCION_CATEGORIA
    await update.message.reply_text("Gracias por tu ayuda 🙌")
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Sesión cancelada.")
    return ConversationHandler.END

# Inicialización segura
async def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Falta la variable de entorno BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()

    # Elimina Webhook anterior por seguridad
    await app.bot.delete_webhook(drop_pending_updates=True)

    conv_handler = ConversationHandler(
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

    app.add_handler(conv_handler)
    logging.info("✅ Alfred está corriendo en Render.")
    await app.run_polling()

# Sin uso de asyncio.run para evitar conflictos con Render
import asyncio
asyncio.run(run_bot())
