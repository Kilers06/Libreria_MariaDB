# Libreria_MariaDB
Requisitos
- Python 3.10 o superior (recomendado).
- Docker Desktop instalado y abierto (en Windows) o Docker Engine con Compose en Linux/macOS.
- Visual Studio Code.
  
Instalación de MariaDB: en este proyecto utilizamos Docker para descargar y ejecutar la imagen oficial mariadb:11. Consulta Docker Desktop para instalar Docker en tu sistema operativo.

1. Abrir el proyecto y preparar MariaDB con Docker
Abre la carpeta del repositorio en VS Code y luego Terminal → New Terminal.

Configuramos el protecto desde cero, se crea un archivo compose.yaml junto al archivo Python con este contenido, lo siguiente es un ejemplo.

services:
  db:
    image: mariadb:11
    container_name: biblioteca_db
    restart: unless-stopped
    environment:
      MARIADB_ROOT_PASSWORD: clave_root_de_ejemplo
    ports:
      - "127.0.0.1:3306:3306"
    volumes:
      - biblioteca_data:/var/lib/mysql

volumes:
  biblioteca_data:

volvemos a abrir la terminal y ingresamos los siguientes comandos
docker compose up -d
docker ps

Esto descarga la imagen y levanta MariaDB. Cambia clave_root_de_ejemplo por una contraseña propia antes de crear el contenedor. El archivo compose.yaml mostrado es una referencia para nuevas instalaciones; si ya tienes uno funcionando, conserva su configuración.


2. Creamos la base de datos y el usuario
En la terminal de VS Code entra al cliente MariaDB del contenedor:
   docker exec -it biblioteca_db mariadb -u root -p
Escribe la contraseña de root definida en tu contenedor. Una vez dentro del cliente MariaDB, ejecuta los siguientes comandos SQL:

CREATE DATABASE IF NOT EXISTS biblioteca
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'biblioteca_user'@'%'
  IDENTIFIED BY 'tu_clave_segura';

GRANT ALL PRIVILEGES ON biblioteca.*
  TO 'biblioteca_user'@'%';

SHOW DATABASES;
EXIT;

Sustituye tu_clave_segura por la contraseña que configurarás también en Python. Si el usuario ya existe, CREATE USER IF NOT EXISTS no cambia su contraseña; reutiliza la que tiene o ajústala conscientemente con ALTER USER.

3. Creamos la tabla "libros"
El archivo Liberiria_MariaDB.py tiene el modelo ORM Libro y ejecuta Base.metadata.create_all(engine) al iniciar. Por eso la tabla libros se crea automáticamente, siempre que la base de datos biblioteca exista y las credenciales sean correctas.

Como referencia, el SQL equivalente para crearla manualmente sería:
USE biblioteca;

CREATE TABLE IF NOT EXISTS libros (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    autor VARCHAR(255) NOT NULL,
    genero VARCHAR(100) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    CONSTRAINT uq_libro_titulo_autor UNIQUE (titulo, autor),
    CONSTRAINT ck_libro_estado CHECK (estado IN ('leído', 'no leído'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

No hace falta ejecutar el SQL manual si dejas que el ORM cree la tabla. Para verificarla, vuelve a entrar en MariaDB y ejecuta USE biblioteca;, SHOW TABLES; y DESCRIBE libros;.

4. Dependencias de Python
Desde la terminal integrada de VS Code, en la carpeta donde está el archivo requirements.txt, ejecuta:
python -m pip install -r requirements.txt
Las dependencias son SQLAlchemy y PyMySQL.

6. Configurar la cadena de conexión
El programa usa esta estructura de conexión:
mysql+pymysql://USUARIO:CONTRASEÑA@HOST:PUERTO/BASE_DE_DATOS
En lugar de escribir la contraseña en el código, la aplicación lee variables de entorno. Para ejecutar Python desde Windows/VS Code y conectarse con MariaDB dentro de Docker (puerto 3306 publicado), introduce en la terminal PowerShell:

$env:DB_HOST="localhost"
$env:DB_PORT="3306"
$env:DB_NAME="biblioteca"
$env:DB_USER="biblioteca_user"
$env:DB_PASSWORD="tu_clave_segura"

Usa la misma contraseña que asignaste al usuario SQL en el paso 2. Estos valores duran mientras esté abierta esa terminal. En Linux/macOS usa export DB_HOST=localhost y del mismo modo para las otras variables.

6. Ejecutar la aplicación
Con Docker en ejecución, MariaDB disponible y las variables configuradas en esa misma terminal de VS Code:
python Liberiria_MariaDB.py

Se mostrará el menú:
====== GESTOR DE BIBLIOTECA ======
1. Agregar libro
2. Actualizar libro
3. Eliminar libro
4. Ver todos los libros
5. Buscar libros
6. Salir
