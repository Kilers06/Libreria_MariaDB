"""
Gestor de biblioteca con MariaDB y SQLAlchemy (ORM).

Requisitos:
    pip install sqlalchemy pymysql

Configuración (variables de entorno, con valores por defecto para desarrollo):
    DB_HOST      (por defecto: localhost)
    DB_PORT      (por defecto: 3306)
    DB_NAME      (por defecto: biblioteca)
    DB_USER      (por defecto: biblioteca_user)
    DB_PASSWORD  (por defecto: cambia_esta_clave)
"""

import os
import sys

from sqlalchemy import CheckConstraint, String, UniqueConstraint, create_engine, or_, select
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


# Configuración


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "biblioteca")
DB_USER = os.getenv("DB_USER", "biblioteca_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cambia_esta_clave")

ESTADOS_VALIDOS = ("leído", "no leído")

CAMPOS_EDITABLES = {
    "1": ("titulo", "Título"),
    "2": ("autor", "Autor"),
    "3": ("genero", "Género"),
    "4": ("estado", "Estado de lectura"),
}


def crear_engine():
    """Crea el engine de SQLAlchemy para MariaDB (driver PyMySQL)."""
    # URL.create escapa correctamente caracteres especiales en la contraseña.
    url = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        query={"charset": "utf8mb4"},
    )
    return create_engine(url, pool_pre_ping=True, echo=False)



# Modelo ORM


class Base(DeclarativeBase):
    pass


class Libro(Base):
    __tablename__ = "libros"
    __table_args__ = (
        UniqueConstraint("titulo", "autor", name="uq_libro_titulo_autor"),
        CheckConstraint("estado IN ('leído', 'no leído')", name="ck_libro_estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    autor: Mapped[str] = mapped_column(String(255), nullable=False)
    genero: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)



# Utilidades de entrada / salida


def mostrar_libro(libro):
    """Imprime un libro en una sola línea."""
    print(
        f"ID: {libro.id} | Título: {libro.titulo} | "
        f"Autor: {libro.autor} | Género: {libro.genero} | Estado: {libro.estado}"
    )


def pedir_texto(mensaje):
    """Pide un texto y repite la pregunta hasta que no esté vacío."""
    while True:
        texto = input(mensaje).strip()
        if texto:
            return texto
        print("El valor no puede estar vacío.")


def pedir_estado(mensaje):
    """Pide el estado de lectura y repite hasta que sea válido."""
    while True:
        estado = input(mensaje).strip().lower()
        # Aceptamos también la versión sin tilde
        estado = estado.replace("leido", "leído")
        if estado in ESTADOS_VALIDOS:
            return estado
        print("Estado no válido. Escribe 'leído' o 'no leído'.")


def pedir_id(mensaje):
    """Pide un ID numérico. Devuelve None si no es válido."""
    try:
        return int(input(mensaje))
    except ValueError:
        print("Debes ingresar un ID numérico.")
        return None



# Operaciones CRUD


def agregar_libro(session):
    print("\n--- AGREGAR LIBRO ---")

    titulo = pedir_texto("Título: ")
    autor = pedir_texto("Autor: ")
    genero = pedir_texto("Género: ")
    estado = pedir_estado("¿Leído o no leído?: ")

    session.add(Libro(titulo=titulo, autor=autor, genero=genero, estado=estado))
    session.commit()
    print("Libro agregado correctamente.")


def listar_libros(session):
    print("\n--- LISTADO DE LIBROS ---")

    libros = session.scalars(select(Libro).order_by(Libro.id)).all()

    if not libros:
        print("No hay libros registrados.")
        return

    for libro in libros:
        mostrar_libro(libro)


def buscar_libros(session):
    print("\n--- BUSCAR LIBROS ---")

    busqueda = pedir_texto("Escribe el título, autor o género: ")
    patron = f"%{busqueda}%"

    consulta = (
        select(Libro)
        .where(
            or_(
                Libro.titulo.like(patron),
                Libro.autor.like(patron),
                Libro.genero.like(patron),
            )
        )
        .order_by(Libro.id)
    )
    resultados = session.scalars(consulta).all()

    if not resultados:
        print("No se encontraron libros.")
        return

    for libro in resultados:
        mostrar_libro(libro)


def actualizar_libro(session):
    print("\n--- ACTUALIZAR LIBRO ---")

    listar_libros(session)

    id_libro = pedir_id("\nIngresa el ID del libro que deseas modificar: ")
    if id_libro is None:
        return

    libro = session.get(Libro, id_libro)
    if libro is None:
        print("No existe un libro con ese ID.")
        return

    print("\n¿Qué deseas modificar?")
    for numero, (_, nombre) in CAMPOS_EDITABLES.items():
        print(f"{numero}. {nombre}")

    opcion = input("Selecciona una opción: ").strip()

    if opcion not in CAMPOS_EDITABLES:
        print("Opción no válida.")
        return

    campo, _ = CAMPOS_EDITABLES[opcion]

    if campo == "estado":
        nuevo_valor = pedir_estado("Ingresa el nuevo estado (leído / no leído): ")
    else:
        nuevo_valor = pedir_texto("Ingresa el nuevo valor: ")

    setattr(libro, campo, nuevo_valor)
    session.commit()
    print("Libro actualizado correctamente.")


def eliminar_libro(session):
    print("\n--- ELIMINAR LIBRO ---")

    listar_libros(session)

    id_libro = pedir_id("\nIngresa el ID del libro que deseas eliminar: ")
    if id_libro is None:
        return

    libro = session.get(Libro, id_libro)
    if libro is None:
        print("No existe un libro con ese ID.")
        return

    confirmacion = input(f"¿Deseas eliminar '{libro.titulo}'? (s/n): ").strip().lower()

    if confirmacion == "s":
        session.delete(libro)
        session.commit()
        print("Libro eliminado correctamente.")
    else:
        print("Eliminación cancelada.")

# Menú

def mostrar_menu():
    print("\n====== GESTOR DE BIBLIOTECA ======")
    print("1. Agregar libro")
    print("2. Actualizar libro")
    print("3. Eliminar libro")
    print("4. Ver todos los libros")
    print("5. Buscar libros")
    print("6. Salir")


def ejecutar_accion(engine, accion):
    """
    Ejecuta una acción con su propia sesión y maneja los errores de base de datos.
    Ante cualquier error se hace rollback y el programa sigue funcionando.
    """
    with Session(engine) as session:
        try:
            accion(session)
        except IntegrityError as error:
            session.rollback()
            print("Error de integridad: el libro ya existe (mismo título y autor) "
                  "o los datos no cumplen las restricciones de la tabla.")
            print(f"Detalle: {error.orig}")
        except OperationalError as error:
            session.rollback()
            print("Error de conexión con la base de datos. "
                  "Verifica que MariaDB esté en ejecución.")
            print(f"Detalle: {error.orig}")
        except SQLAlchemyError as error:
            session.rollback()
            print(f"Error inesperado en la base de datos: {error}")


def menu(engine):
    acciones = {
        "1": agregar_libro,
        "2": actualizar_libro,
        "3": eliminar_libro,
        "4": listar_libros,
        "5": buscar_libros,
    }

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "6":
            print("¡Gracias por utilizar el gestor de biblioteca!")
            break

        accion = acciones.get(opcion)
        if accion:
            ejecutar_accion(engine, accion)
        else:
            print("Opción no válida. Intenta nuevamente.")


def main():
    engine = crear_engine()
    try:
        # Crea las tablas si no existen (también valida la conexión).
        Base.metadata.create_all(engine)
    except OperationalError as error:
        print("No se pudo conectar a MariaDB.")
        print(f"  Host: {DB_HOST}:{DB_PORT} | Base de datos: {DB_NAME} | Usuario: {DB_USER}")
        print("  Revisa que el servicio esté activo, que la base de datos exista "
              "y que el usuario y la contraseña sean correctos.")
        print(f"  Detalle: {error.orig}")
        sys.exit(1)
    except SQLAlchemyError as error:
        print(f"Error al preparar la base de datos: {error}")
        sys.exit(1)

    try:
        menu(engine)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido. ¡Hasta luego!")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()