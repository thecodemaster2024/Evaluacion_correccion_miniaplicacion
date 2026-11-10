"""BASE EDUCATIVA INSEGURA. Corregir los TODO antes de la entrega."""
from copy import error
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "inventario.json"
USUARIOS = RAIZ / "usuarios.json"
LOG = RAIZ / "auditoria.jsonl"

# TODO: (Listo!)controlar archivo ausente y JSON inválido. No sobrescribirlos.
def cargar_inventario():
    try:
        return json.loads(DATOS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo de inventario: {DATOS}")
    except json.JSONDecodeError as error:
        print(
            f"Error: el JSON del inventario no es válido "
            f"(línea {error.lineno}, columna {error.colno})."
        )
    return None

def guardar_inventario(productos):
    DATOS.write_text(json.dumps(productos, indent=2), encoding="utf-8")

# TODO (Listo!): guardar un objeto JSON por línea; fecha/hora, usuario, acción,
    # resultado y detalles no sensibles. Nunca guardar contraseña ni hash.
def registrar_evento(usuario, accion, resultado, **detalles):
    try:
        from datetime import datetime

        evento = {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "usuario": usuario,
            "accion": accion,
            "resultado": resultado,
            "detalles": {k: v for k, v in detalles.items() if k not in {"clave", "hash"}}
        }

        with LOG.open("a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except Exception:
        pass

# TODO (Listo!): integrar seguridad.py y migrar usuarios.json sin claves legibles.
def autenticar(nombre, clave):
    try:
        from seguridad import verificar_clave
        usuarios = json.loads(USUARIOS.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        print("No se pudo leer el archivo de usuarios.")
        return None
    

    for usuario in usuarios:
        if usuario.get("usuario") == nombre and verificar_clave(usuario.get("hash", ""), clave):
            registrar_evento(nombre, "login", "exitoso")
            return {"usuario": nombre, "rol": usuario.get("rol", "user")}
    # TODO (Listo!): registrar también el intento fallido.
    registrar_evento(nombre, "login", "fallido", motivo="credenciales_invalidas")
    print("Credenciales incorrectas.")
    return None


def consultar_inventario(sesion):
    # TODO (Listo!): rechazar si no existe sesión válida.
    if (
        not isinstance(sesion, dict)
        or not sesion.get("usuario")
        or sesion.get("rol") not in {"admin", "user"}
    ):
        usuario = sesion.get("usuario", "anonimo") if isinstance(sesion, dict) else "anonimo"
        print("No autorizado.")
        registrar_evento(usuario, "consultar", "fallido", motivo="sesion_invalida")
        return False

    productos = cargar_inventario()
    for producto in productos:
        print(producto["id"], producto["nombre"], producto["cantidad"])
    return True

# TODO (Listo!): verificar sesión y rol AQUÍ, antes de modificar.
# TODO (Listo!): validar entero entre 0 y 1000, sin interrumpir el programa.
def modificar_cantidad(sesion, identificador, entrada):
    if (
        not isinstance(sesion, dict)
        or not sesion.get("usuario")
        or sesion.get("rol") != "admin"
    ):
        usuario = sesion.get("usuario", "anonimo") if isinstance(sesion, dict) else "anonimo"
        print("No autorizado.")
        registrar_evento(usuario, "modificar", "fallido", motivo="sin_permiso")
        return False

    try:
        cantidad = int(entrada)
    except ValueError:
        print("La cantidad debe ser un entero.")
        registrar_evento(sesion["usuario"], "modificar", "fallido", motivo="cantidad_invalida")
        return False

    if not 0 <= cantidad <= 1000:
        print("La cantidad debe estar entre 0 y 1000.")
        registrar_evento(sesion["usuario"], "modificar", "fallido", motivo="cantidad_fuera_de_rango")
        return False

    productos = cargar_inventario()
    for producto in productos:
        if producto["id"] == identificador:
            anterior = producto["cantidad"]
            producto["cantidad"] = cantidad
            guardar_inventario(productos)
            registrar_evento(
                sesion["usuario"], "modificar", "exitoso",
                producto=identificador, anterior=anterior, nueva=cantidad
            )
            print("Cantidad actualizada.")
            return True

    print("Identificador inexistente.")
    registrar_evento(sesion["usuario"], "modificar", "fallido", motivo="id_inexistente", producto=identificador)
    # TODO (Listo!): informar identificador inexistente, sin crear productos.
    return False

#==============================================================================
def main():
    print("Inventario académico — BASE CON DEBILIDADES")
    print("Estudiante:", input("Escriba su nombre: "))
    sesion = None
    while True:
        if sesion is None:
            nombre = input("Usuario (o salir): ")
            if nombre == "salir":
                break
            sesion = autenticar(nombre, input("Contraseña de prueba: "))
            continue
        print("1. Consultar | 2. Modificar | 3. Cerrar sesión | 0. Salir")
        opcion = input("Opción: ")
        if opcion == "1":
            consultar_inventario(sesion)
        elif opcion == "2":
            identificador = input("ID del producto: ")
            entrada = input("Nueva cantidad: ")
            modificar_cantidad(sesion, identificador, entrada)
        elif opcion == "3":
            sesion = None
        elif opcion == "0":
            break
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    main()
