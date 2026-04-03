# Sistema de Gestión de Identidades Digitales

Proyecto desarrollado para la materia **Uso de Álgebras Modernas para Seguridad y Criptografía (Gpo 601)**.

Este proyecto consiste en el desarrollo de una aplicación de escritorio en Python que implementa un **sistema de gestión de identidades digitales**, simulando el funcionamiento básico de una **Infraestructura de Clave Pública (PKI)**.

El sistema permite registrar usuarios, generar claves criptográficas, emitir certificados digitales, firmar documentos y controlar el acceso a funcionalidades mediante distintos niveles de autorización.


# Autores

* Alicia Josefina de la Garza Montelongo — A01198742
* Gisel Regina Benítez Calvillo — A00228137
* Lillianne Sepúlveda Cuevas — A00839109
* Axel Xavier Olivar Lozano — A01286176
* Jorge Eduardo Avila Montoya — A01410275


# Descripción del sistema

El sistema implementa diferentes mecanismos de seguridad informática basados en criptografía moderna para gestionar identidades digitales dentro de una organización.

Entre sus funcionalidades principales se encuentran:

* Registro de usuarios
* Generación automática de claves criptográficas
* Emisión de certificados digitales
* Firma digital de mensajes y archivos
* Verificación de firmas digitales
* Autenticación con múltiples factores (OTP)
* Control de acceso basado en roles
* Registro de actividades del sistema (logs)
* Panel de administración para gestión de usuarios

El sistema fue desarrollado en **Python** utilizando una arquitectura modular que separa la interfaz gráfica, la lógica del sistema, los módulos criptográficos y la base de datos.


# Tecnologías utilizadas

El proyecto utiliza diversas herramientas y bibliotecas del ecosistema de Python.

Principales tecnologías:

* **Python 3**
* **Tkinter** — interfaz gráfica
* **SQLite** — base de datos local
* **Cryptography Library** — operaciones criptográficas
* **Hashlib** — funciones hash
* **PBKDF2** — almacenamiento seguro de contraseñas


# Algoritmos criptográficos utilizados

El sistema utiliza algoritmos criptográficos modernos para garantizar la seguridad de la información.

### RSA (2048 bits)

Se utiliza para la generación de pares de claves públicas y privadas. Cada usuario registrado recibe automáticamente un par de claves RSA que se utilizan para generar y verificar firmas digitales.

### SHA-256

Se utiliza como función hash para garantizar la integridad de la información y para el almacenamiento seguro de contraseñas mediante el algoritmo PBKDF2.

### RSA-PSS

El esquema de padding **PSS (Probabilistic Signature Scheme)** se utiliza al generar firmas digitales con RSA para incrementar la seguridad del sistema y evitar ataques criptográficos.


# Arquitectura del sistema

El sistema está organizado en distintos módulos que separan responsabilidades dentro del programa.

```
Proyecto
│
├── auth
│   ├── auth.py
│   ├── mfa.py
│   └── permissions.py
│
├── crypto
│   ├── keys.py
│   ├── signature.py
│   └── certificate.py
│
├── db
│   ├── database.py
│   ├── logs.py
│   └── admin_queries.py
│
├── ui
│   └── login_window.py
│
├── config
│   └── paths.py
│
├── data
│   └── users
│
└── main.py
```


# Estructura de almacenamiento

Cada usuario tiene su propio directorio dentro del sistema para almacenar sus recursos criptográficos.

```
data/
 └── users/
     └── username/
         ├── keys/
         │   ├── username_private.pem
         │   └── username_public.pem
         │
         ├── certificates/
         │   └── username_cert.json
         │
         └── signatures/
             └── signature_timestamp.sig
```

Esto permite mantener una estructura organizada y facilita la gestión de identidades digitales.


# Control de acceso

El sistema implementa **Control de Acceso Basado en Roles (RBAC)**.

Se definieron cuatro niveles de autorización:

| Nivel   | Rol                | Permisos                                  |
| ------- | ------------------ | ----------------------------------------- |
| Nivel 4 | Personal externo   | Consultar información                     |
| Nivel 3 | Personal operativo | Consultar y editar información            |
| Nivel 2 | Coordinadores      | Consultar, editar y autorizar información |
| Nivel 1 | Administradores    | Acceso completo al sistema                |

Los administradores cuentan además con funcionalidades adicionales como:

* Gestión de usuarios
* Cambio de roles
* Visualización de logs del sistema



# Funcionalidades principales

### Registro de usuarios

Permite registrar nuevas identidades digitales dentro del sistema. Durante el registro se generan automáticamente:

* Par de claves RSA
* Certificado digital del usuario



### Autenticación segura

El sistema implementa autenticación en dos pasos:

1. Contraseña protegida con PBKDF2 + SHA256
2. Código OTP (One Time Password)



### Firma digital

Los usuarios pueden firmar digitalmente:

* Mensajes de texto
* Archivos

Las firmas se generan utilizando **RSA + PSS + SHA256**.



### Verificación de firmas

El sistema permite verificar la autenticidad de mensajes o archivos firmados mediante la clave pública del usuario.



### Certificados digitales

Cada usuario posee un certificado digital que contiene:

* Identidad del usuario
* Fecha de emisión
* Fecha de expiración
* Hash de verificación



### Registro de actividades

Todas las acciones importantes del sistema se almacenan en una base de datos SQLite para fines de auditoría.



# Instalación

1. Clonar el repositorio

```
git clone https://github.com/usuario/repositorio.git
```

2. Instalar dependencias

```
pip install cryptography
```

3. Ejecutar el sistema

```
python main.py
```

---

# Limitaciones del proyecto

Este sistema es una **implementación académica** y presenta algunas limitaciones:

* No implementa el estándar completo X.509
* No incluye infraestructura de certificación real
* No se integra con servicios externos
* No se implementa infraestructura en la nube

---

# Trabajo futuro

Algunas mejoras posibles para el sistema incluyen:

* Implementación de certificados X.509 completos
* Integración con servicios en la nube
* Mejora de la interfaz gráfica
* Implementación de revocación de certificados
* Integración con sistemas de autenticación externos

---

# Licencia

Este proyecto fue desarrollado con fines académicos para la materia **Uso de Álgebras Modernas para Seguridad y Criptografía**.

