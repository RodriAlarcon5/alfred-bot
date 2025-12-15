import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

# --- Utilidad: /GroupID ---
async def group_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    await update.message.reply_text(f"Chat type: {chat.type}\nChat ID: {chat.id}")
# --- Fin utilidad ---

# Estados de conversación
SELECCION_CIUDAD, VERIFICAR_CIUDAD = range(2)
SELECCION_CATEGORIA, RECIBIR_IMAGENES, SIGUE_O_NO = range(3, 6)

# Opciones
CIUDADES = {
    "1": "Ciudad de México",
    "2": "Guadalajara",
    "3": "Monterrey",
    "4": "Puebla",
    "5": "Chihuahua",
    "6": "Ciudad Juárez",
    "7": "Hermosillo",
    "8": "Saltillo",
    "9": "Mérida"
}

CATEGORIAS = {
    "1": "App Naranja 🍊 – Incentivos",
    "2": "App Negra ⚫ – Incentivos",
    "3": "App Negra ⚫ – Desglose de la tarifa del usuario",
    "4": "App Negra ⚫ – Recibos de viaje",
    "5": "App Verde 🟢 - Incentivos",
    "6": "App Verde 🟢 - Recibos de viaje"
}

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Grupos
GROUP_ID = int(os.getenv("GROUP_ID", "-1002642749020"))        # Grupo principal
EXTRA_GROUP_ID = int(os.getenv("EXTRA_GROUP_ID", "-1002624521213"))  # Desglose/Recibos
CJ_GROUP_ID = -1002979170948  # Grupo compartido para Ciudad Juárez / Saltillo / Hermosillo

# Funciones del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hola, soy *Alfred* 🤖, estaré ayudándote a recibir tus screenshots. ¡Gracias por tu tiempo! 🙌\n\n"
        "Vamos a comenzar. Por favor selecciona la *ciudad donde vives* escribiendo el número correspondiente:\n\n"
        "1. Ciudad de México\n2. Guadalajara\n3. Monterrey\n4. Puebla\n5. Chihuahua\n6. Ciudad Juárez\n7. Hermosillo\n8. Saltillo\n9. Mérida",
        parse_mode="Markdown"
    )
    return SELECCION_CIUDAD


async def guardar_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    seleccion = update.message.text.strip()
    if seleccion not in CIUDADES:
        await update.message.reply_text(f"Selecciona una opción válida: {', '.join(CIUDADES.keys())}.")
        return SELECCION_CIUDAD
    context.user_data["ciudad"] = CIUDADES[seleccion]
    await update.message.reply_text("Escribe tu número celular con el que estás registrado en la app:")
    return VERIFICAR_CIUDAD


async def verificar_ciudad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text(
        "Selecciona la categoría:\n"
        "1. App Naranja 🍊 – Incentivos\n"
        "2. App Negra ⚫ – Incentivos\n"
        "3. App Negra ⚫ – Desglose de la tarifa del usuario\n"
        "4. App Negra ⚫ – Recibos de viaje\n"
        "5. App Verde 🟢 - Incentivos\n"
        "6. App Verde 🟢 - Recibos de viaje"
    )
    return SELECCION_CATEGORIA


async def guardar_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    seleccion = update.message.text.strip()
    if seleccion not in CATEGORIAS:
        await update.message.reply_text(f"Selecciona una opción válida: {', '.join(CATEGORIAS.keys())}.")
        return SELECCION_CATEGORIA
    context.user_data["categoria"] = CATEGORIAS[seleccion]
    await update.message.reply_text("Ahora envíame las capturas. Cuando termines escribe 'listo'.")
    return RECIBIR_IMAGENES


async def recibir_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text and update.message.text.lower() == "listo":
        await update.message.reply_text("¿Deseas subir otra categoría? (si/no)")
        return SIGUE_O_NO

    if update.message.photo:
        foto = update.message.photo[-1]
        ciudad_actual = context.user_data.get("ciudad", "")
        categoria_actual = context.user_data.get("categoria", "")
        caption = (
            f"{context.user_data['nombre']}\n"
            f"{ciudad_actual}\n"
            f"{categoria_actual}"
        )

        # Ciudad Juárez, Saltillo y Hermosillo usan el MISMO grupo
        if ciudad_actual in {"Ciudad Juárez", "Saltillo", "Hermosillo", "Mérida"}:
            await context.bot.send_photo(chat_id=CJ_GROUP_ID, photo=foto.file_id, caption=caption)
        else:
            # Enviar al grupo principal
            await context.bot.send_photo(chat_id=GROUP_ID, photo=foto.file_id, caption=caption)

            # Enviar al grupo extra si la categoría es Desglose o Recibos
            if categoria_actual.startswith("App Negra ⚫ – Desglose") or categoria_actual.startswith("App Negra ⚫ – Recibos"):
                await context.bot.send_photo(chat_id=EXTRA_GROUP_ID, photo=foto.file_id, caption=caption)

        await update.message.reply_text("📸 Imagen enviada correctamente. Puedes enviar otra o escribe 'listo' si ya terminaste")
    else:
        await update.message.reply_text("Envía una imagen o escribe 'listo' si ya terminaste.")
    return RECIBIR_IMAGENES


async def decidir_siguiente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() in {"si", "sí"}:
        await update.message.reply_text(
            "Selecciona la categoría:\n"
            "1. App Naranja 🍊 – Incentivos\n"
            "2. App Negra ⚫ – Incentivos\n"
            "3. App Negra ⚫ – Desglose de la tarifa del usuario\n"
            "4. App Negra ⚫ – Recibos de viaje\n"
            "5. App Verde 🟢 - Incentivos\n"
            "6. App Verde 🟢 - Recibos de viaje"
        )
        return SELECCION_CATEGORIA
    await update.message.reply_text("Gracias por tu ayuda 🙌")
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Sesión cancelada.")
    return ConversationHandler.END


# Código principal para Web Service
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Falta la variable de entorno BOT_TOKEN")

    application = ApplicationBuilder().token(token).build()

    # Handler del comando /GroupID
    application.add_handler(CommandHandler("GroupID", group_id))

    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                SELECCION_CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_ciudad)],
                VERIFICAR_CIUDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, verificar_ciudad)],
                SELECCION_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_categoria)],
                RECIBIR_IMAGENES: [
                    MessageHandler(filters.PHOTO, recibir_imagen),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_imagen),
                ],
                SIGUE_O_NO: [MessageHandler(filters.TEXT & ~filters.COMMAND, decidir_siguiente)],
            },
            fallbacks=[CommandHandler("cancel", cancelar)],
        )
    )

    logging.info("✅ Alfred está corriendo en Render (sin asyncio.run).")
    application.run_polling()
