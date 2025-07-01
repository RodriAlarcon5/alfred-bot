import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
import os

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
    return RECIBIR_IMAGENES

async def texto_listo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("¡Gracias! Tus imágenes han sido recibidas.")
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECCION_CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_ciudad)],
            VERIFICAR_CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, verificar_ciudad)],
            SELECCION_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_categoria)],
            RECIBIR_IMAGENES: [
                MessageHandler(filters.PHOTO, recibir_imagen),
                MessageHandler(filters.TEXT & filters.Regex("(?i)^listo$"), texto_listo)
            ],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
