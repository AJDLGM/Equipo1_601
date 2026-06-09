# Sistema de Gestión de Identidades Digitales (Casa Monarca)

## Descripción General

El Sistema de Gestión de Identidades Digitales (Casa Monarca) es una aplicación cliente-servidor que simula una Infraestructura de Clave Pública (PKI) para la administración de identidades digitales, certificados electrónicos y firma digital de documentos.

El sistema permite gestionar usuarios, generar material criptográfico, firmar documentos electrónicamente, verificar firmas digitales y administrar el ciclo de vida completo de certificados digitales mediante un esquema de control de acceso basado en roles.

Este proyecto fue desarrollado como parte de la materia **Uso de Álgebras Modernas para Seguridad y Criptografía**.

---

## Autores

| Nombre                                 | Matrícula |
| -------------------------------------- | --------- |
| Alicia Josefina de la Garza Montelongo | A01198742 |
| Gisel Regina Benítez Calvillo          | A00228137 |
| Lillianne Sepúlveda Cuevas             | A00839109 |
| Axel Xavier Olivar Lozano              | A01286176 |
| Jorge Eduardo Avila Montoya            | A01410275 |

---

## Objetivo

Desarrollar un sistema que simule el funcionamiento básico de una Infraestructura de Clave Pública (PKI), permitiendo:

* Gestión de identidades digitales.
* Generación de claves criptográficas.
* Emisión de certificados digitales.
* Firma electrónica de documentos.
* Verificación de autenticidad e integridad.
* Revocación de certificados.
* Control de acceso mediante roles.
* Auditoría de actividades del sistema.

---

## Funcionalidades

### Gestión de usuarios

* Registro de usuarios mediante autoservicio.
* Aprobación o rechazo de solicitudes por parte del administrador.
* Alta directa de usuarios.
* Revocación de certificados.
* Baja de identidades.
* Consulta de usuarios activos y pendientes.

### Criptografía

* Generación automática de claves RSA de 2048 bits.
* Emisión de certificados digitales.
* Verificación de certificados.
* Gestión de claves públicas y privadas.

### Firma digital

* Firma de documentos DOCX.
* Firma de documentos PDF.
* Firma de archivos genéricos mediante contenedores seguros.
* Verificación de integridad y autenticidad.
* Firma múltiple mediante rutas de aprobación.

### Control de acceso

El sistema implementa un modelo RBAC (Role-Based Access Control) con cuatro niveles:

| Rol           | Descripción                                       |
| ------------- | ------------------------------------------------- |
| Externo       | Solicita firmas y consulta documentos             |
| Operativo     | Gestiona y canaliza solicitudes                   |
| Coordinador   | Firma documentos dentro de una ruta de aprobación |
| Administrador | Gestiona usuarios, certificados y configuración   |

### Auditoría

* Registro de actividades del sistema.
* Consulta de logs.
* Seguimiento de acciones realizadas por cada usuario.

---

## Arquitectura

El sistema sigue una arquitectura cliente-servidor.

### Cliente

Aplicación de escritorio desarrollada con Tkinter.

Responsabilidades:

* Inicio de sesión.
* Gestión de usuarios.
* Firma local de documentos.
* Verificación de documentos.
* Interacción con la API REST.

### Servidor

API REST desarrollada con Flask.

Responsabilidades:

* Autenticación.
* Gestión de usuarios.
* Emisión de certificados.
* Administración de solicitudes.
* Persistencia de información.

### Base de datos

SQLite es utilizada para almacenar:

* Usuarios.
* Certificados.
* Claves públicas.
* Solicitudes de firma.
* Rutas de firma.
* Registros de auditoría.

---

## Tecnologías Utilizadas

| Tecnología   | Uso                             |
| ------------ | ------------------------------- |
| Python 3     | Lenguaje principal              |
| Flask        | API REST                        |
| Tkinter      | Interfaz gráfica                |
| SQLite       | Base de datos                   |
| Cryptography | Operaciones criptográficas      |
| python-docx  | Manipulación de documentos Word |
| pypdf        | Manipulación de documentos PDF  |
| ReportLab    | Generación de PDFs              |
| Requests     | Comunicación HTTP               |
| Pillow       | Manejo de imágenes              |
| PyInstaller  | Generación del ejecutable       |
| Railway      | Despliegue del servidor         |

---

## Estructura del Proyecto

```text
Equipo1_601/
│
├── auth/
│   ├── auth.py
│   ├── permissions.py
│   └── mfa.py
│
├── crypto/
│   ├── keys.py
│   ├── certificate.py
│   └── signature.py
│
├── db/
│   ├── database.py
│   ├── admin_queries.py
│   ├── signing_requests.py
│   ├── firma_route.py
│   └── logs.py
│
├── server/
│   ├── app.py
│   └── run_server.bat
│
├── client/
│   └── api_client.py
│
├── ui/
│   ├── login_window.py
│   ├── admin_panel.py
│   └── logo_data.py
│
├── config/
│   ├── paths.py
│   └── server_config.py
│
├── assets/
├── docs/
│
├── main.py
├── wsgi.py
├── Procfile
├── requirements.txt
└── SistemaIdentidad.spec
```

---

## Instalación

### Clonar el repositorio

```bash
git clone https://github.com/usuario/repositorio.git
cd repositorio
```

### Crear entorno virtual

```bash
python -m venv venv
```

### Activar entorno virtual

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Ejecución del Servidor

```bash
python server/app.py
```

o

```bash
python wsgi.py
```

El servidor iniciará por defecto en:

```text
http://localhost:5000
```

---

## Ejecución del Cliente

```bash
python main.py
```

---

## Compilación del Cliente

Para generar el ejecutable:

```bash
build.bat
```

o

```bash
pyinstaller SistemaIdentidad.spec
```

---

## Flujo General del Sistema

1. El usuario crea una cuenta.
2. El administrador aprueba la solicitud.
3. Se generan automáticamente las claves RSA y el certificado digital.
4. El usuario descarga su clave privada.
5. El usuario puede solicitar firmas o participar en procesos de aprobación según su rol.
6. Los coordinadores firman los documentos.
7. El sistema verifica la integridad y autenticidad de las firmas.
8. El documento firmado queda disponible para descarga.

---

## Seguridad Implementada

### Autenticación

* PBKDF2-HMAC-SHA256.
* 200,000 iteraciones.
* Salt aleatorio por usuario.

### Firma Digital

* RSA de 2048 bits.
* RSA-PSS.
* SHA-256.

### Certificados

* Certificados digitales firmados.
* Lista de certificados revocados (CRL).

### Sesiones

* Tokens de autenticación.
* Control de acceso basado en roles.

---

## Limitaciones Actuales

* No implementa certificados X.509 completos.
* Las sesiones se almacenan en memoria.
* Las claves privadas no están protegidas mediante passphrase.
* No existe recuperación de contraseña.
* El MFA aún no está integrado al flujo de autenticación.
* No se cuenta con una suite formal de pruebas automatizadas.

---

## Trabajo Futuro

* Implementación de certificados X.509.
* Integración de autenticación multifactor.
* Uso de JWT para sesiones.
* Cifrado de claves privadas mediante passphrase.
* Automatización de pruebas.
* Mejoras en la autorización a nivel de API.
* Optimización de la gestión de archivos y documentos.

---

## Licencia

Este proyecto fue desarrollado con fines académicos para la materia Uso de Álgebras Modernas para Seguridad y Criptografía del Tecnológico de Monterrey.

Su uso, modificación y distribución deben realizarse respetando los lineamientos establecidos por los autores y la institución.
