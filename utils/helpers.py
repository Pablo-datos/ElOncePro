import pandas as pd

def filtrar_microciclos_por_categoria(microciclos_df, temporadas_df, temporada_nombre, categoria):
    """
    Filtra los microciclos que pertenecen a la temporada y categoría seleccionadas.
    """
    temporada_id = temporadas_df[
        (temporadas_df["nombre"] == temporada_nombre) &
        (temporadas_df["categoria"] == categoria)
    ]["id_temporada"].values

    if len(temporada_id) == 0:
        return pd.DataFrame()  # No hay coincidencias

    temporada_id = temporada_id[0]
    return microciclos_df[
        (microciclos_df["id_temporada"] == temporada_id) &
        (microciclos_df["categoria"] == categoria)
    ]

def mostrar_icono_categoria(categoria):
    """
    Devuelve un ícono según la categoría.
    """
    iconos = {
        "Prebenjamín A": "🟡",
        "Prebenjamín B": "🟠",
        "Benjamín A": "🔵",
        "Benjamín B": "🟣",
        "Alevín A": "🟢",
        "Alevín B": "🟤",
        "Infantil A": "🟥",
        "Infantil B": "🟧",
        "Cadete A": "🟦",
        "Cadete B": "🟪",
        "Juvenil": "⬛",
        "Primer Equipo": "⭐",
        "Reserva / Equipo B": "⚪",
    }
    return iconos.get(categoria, "⚽")
