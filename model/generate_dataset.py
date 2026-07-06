"""
Genera el dataset sintético de mensajes spam/ham usado para entrenar el
clasificador (model/data/spam.csv).

¿Por qué un dataset sintético? Este proyecto se desarrolló en un entorno sin
acceso a internet para descargar datasets públicos (p. ej. SMS Spam
Collection de la UCI). Para no bloquear el desarrollo se generó un dataset
propio, programático y reproducible (semilla fija) a partir de plantillas
realistas de mensajes en español, con sustitución aleatoria de nombres,
horarios, montos, marcas y enlaces.

Se incluyen deliberadamente "casos trampa" (p. ej. mensajes ham que usan la
palabra "gratis"/"free" en un contexto normal) para poder evaluar si el
modelo aprende patrones reales y no solo coincidencias de palabras sueltas.
Ver docs/VALIDACION_PRUEBAS.md para el análisis de resultados y limitaciones.

Uso:
    python -m model.generate_dataset
"""
import csv
import random
from pathlib import Path

random.seed(42)

DATA_PATH = Path(__file__).parent / "data" / "spam.csv"

names = ["Juan", "María", "Carlos", "Ana", "Luis", "Sofía", "Pedro", "Laura",
         "Diego", "Valentina", "Miguel", "Camila", "Jorge", "Fernanda", "Andrés"]
times = ["a las 5", "mañana", "el viernes", "en la tarde", "a las 8am",
         "el sábado", "en 20 minutos", "después de clase", "el lunes"]
places = ["la oficina", "el café de siempre", "tu casa", "el gimnasio",
          "la universidad", "el centro comercial", "la reunión"]
amounts = ["$500", "$1,000", "$2,500", "$10,000", "$99", "$250", "$5,000"]
brands = ["NetFlixPro", "AmazPrime", "BancoSeguro", "TeleMovil", "SuperCredit",
          "GanaYa", "ClickPremio", "FastLoan", "MegaPromo", "CryptoBoom"]
links = ["http://bit.ly/premio", "http://free-gift.win", "www.reclama-ya.net",
         "http://claim-now.co", "www.oferta-flash.com", "http://gana-hoy.info"]
phones = ["809-555-01" + str(i).zfill(2) for i in range(1, 60)]

ham_templates = [
    "Hola {name}, ¿nos vemos {time} en {place}?",
    "Oye {name}, ¿tienes {time} libre para hablar?",
    "Recuerda que la tarea se entrega {time}, no lo olvides.",
    "{name}, ya llegué a {place}, avísame cuando estés cerca.",
    "Gracias por tu ayuda con el proyecto, quedó muy bien.",
    "¿Vamos a comer algo {time}? Tengo hambre.",
    "El profesor movió la clase para {time}.",
    "{name} dice que la reunión es en {place}, confírmame si puedes ir.",
    "Feliz cumpleaños {name}! Que la pases increíble.",
    "¿Puedes mandarme el archivo del reporte antes de {time}?",
    "Todo listo para la presentación de {time}, ¿nervioso?",
    "Llámame cuando puedas, es sobre lo de {place}.",
    "¿Estás libre esta noche o mejor lo dejamos para {time}?",
    "Ya pagué la renta de este mes, quedamos a mano.",
    "El médico me dio cita {time}, no voy a poder ir a {place}.",
    "Gracias por el regalo, no era necesario pero me encantó.",
    "¿Cómo estuvo tu día? Yo saliendo tarde de {place}.",
    "Nos juntamos en {place} {time}, lleva tu laptop.",
    "Perdón por no contestar antes, estaba en {place}.",
    "¿Ya viste el partido de anoche? Estuvo increíble.",
    "Te dejo el número de mi contador por si lo necesitas: {phone}",
    "Voy a estar fuera de la ciudad {time}, cualquier cosa me escribes.",
    "Mi mamá pregunta si vienes a comer {time}.",
    "El equipo terminó el sprint a tiempo, buen trabajo a todos.",
    "¿Me prestas {amount} hasta el viernes? Te los devuelvo con la quincena.",
    "Actualicé el documento compartido, revisa los cambios cuando puedas.",
    "Hoy hay tráfico pesado camino a {place}, sal con tiempo.",
    "¿Puedes recoger a los niños {time}? Se me hizo tarde en el trabajo.",
    "Excelente clase hoy, aprendí bastante sobre el tema.",
    "{name}, te comparto mis apuntes de la clase de {time}.",
    "Vi que hay una promoción en el supermercado, ¿necesitas algo?",
    "Tranquilo, no pasa nada, lo resolvemos {time}.",
    "El vuelo sale {time}, nos vemos en el aeropuerto.",
    "¿Cuánto quedó el total de la cena? Te transfiero mi parte.",
    "Buen provecho, disfruta tu comida en {place}.",
    "Ya subí las fotos del viaje, échales un ojo cuando puedas.",
    "¿Qué opinas del nuevo horario de {time}? A mí me acomoda bien.",
    "Feliz aniversario, {name}. Gracias por todo este tiempo juntos.",
    "El internet estuvo fallando toda la mañana en {place}.",
    "Ya entregué el pago de {amount} de la universidad, guardé el recibo.",
]

spam_templates = [
    "¡FELICIDADES! Has ganado un premio de {amount}. Reclama ahora en {link}",
    "GANADOR: Tu número fue seleccionado para un premio de {brand}. Click aquí: {link}",
    "URGENTE: Tu cuenta de {brand} será suspendida. Verifica ya en {link}",
    "Consigue un préstamo de {amount} en minutos, sin buros. Aplica en {link}",
    "GRATIS por tiempo limitado: Recarga {amount} en tu celular. Entra a {link}",
    "Oferta exclusiva solo hoy: 90% de descuento en {brand}, no te la pierdas {link}",
    "Confirma tus datos bancarios para recibir tu reembolso de {amount}: {link}",
    "Has sido preseleccionado para un iPhone GRATIS. Reclama en {link} antes de que expire",
    "ALERTA: actividad sospechosa detectada en tu cuenta. Ingresa a {link} para verificar",
    "Invierte {amount} hoy y multiplica tus ganancias con {brand}. Info: {link}",
    "Última oportunidad: tu paquete está retenido, paga {amount} de aduana aquí {link}",
    "CLICK AQUI para reclamar tu premio de {brand} antes de que caduque: {link}",
    "Enhorabuena, tu número ganó la lotería de {brand}. Contacta al {phone}",
    "Aprovecha ya! Créditos aprobados al instante hasta {amount}, sin aval: {link}",
    "Tu suscripción de {brand} fue cancelada, reactívala gratis en {link}",
    "100% GRATIS: Descarga la app y gana {amount} al instante {link}",
    "Señora/Señor, adeuda {amount} al SAT, regularice en {link} o proceda legal",
    "Solo por hoy: Compra 1 y lleva 2 en {brand}, oferta valida en {link}",
    "Estimado cliente, verifique su tarjeta para evitar bloqueo: {link}",
    "¡No lo pienses más! Gana {amount} respondiendo esta encuesta: {link}",
    "Trabaja desde casa y gana {amount} semanales, inscríbete en {link}",
    "Tu envío no pudo entregarse, reprograma pagando {amount} en {link}",
    "FREE GIFT esperándote, no te lo pierdas, reclama en {link} ahora",
    "Se le notifica que tiene una multa pendiente de {amount}, pague en {link}",
    "Últimas horas: crédito preaprobado de {amount}, deposito inmediato {link}",
    "Marca al {phone} para reclamar tu premio de {brand}, oferta vence hoy",
    "IMPORTANTE: actualiza tu método de pago de {brand} en {link} o perderás el servicio",
    "Cliente VIP, tienes acumulado {amount} en puntos. Canjéalos en {link}",
    "Congratulations! You have won {amount} with {brand}, claim now at {link}",
    "Recibe {amount} gratis al registrarte hoy en {brand}: {link}",
]


def fill(template):
    return template.format(
        name=random.choice(names),
        time=random.choice(times),
        place=random.choice(places),
        amount=random.choice(amounts),
        brand=random.choice(brands),
        link=random.choice(links),
        phone=random.choice(phones),
    )


def generate(n_ham=650, n_spam=350):
    rows = []
    seen = set()
    count, attempts = 0, 0
    while count < n_ham and attempts < n_ham * 30:
        attempts += 1
        t = fill(random.choice(ham_templates))
        if t not in seen:
            seen.add(t)
            rows.append(("ham", t))
            count += 1
    count, attempts = 0, 0
    while count < n_spam and attempts < n_spam * 30:
        attempts += 1
        t = fill(random.choice(spam_templates))
        if t not in seen:
            seen.add(t)
            rows.append(("spam", t))
            count += 1
    random.shuffle(rows)
    return rows


def main():
    rows = generate()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "text"])
        writer.writerows(rows)
    n_spam = sum(1 for r in rows if r[0] == "spam")
    n_ham = sum(1 for r in rows if r[0] == "ham")
    print(f"Dataset generado: {len(rows)} filas (ham={n_ham}, spam={n_spam}) -> {DATA_PATH}")


if __name__ == "__main__":
    main()
